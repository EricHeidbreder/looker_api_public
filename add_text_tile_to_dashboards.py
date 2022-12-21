from __future__ import absolute_import

import click
import looker_sdk
import json
from typing import List


sdk = looker_sdk.init40()


def _get_dashboard_list(look_id: int) -> List[int]:
    """Get a list of dashboards from a look."""
    look_data = sdk.run_look(look_id=look_id, result_format="json", apply_vis=True)
    return [v for d in json.loads(look_data) for _, v in d.items()]


def add_legal_text_tile(dashboard_num: int, dashboard_list_initial: List[int], is_dryrun: bool) -> None:
    """Add a text tile to dashboards, if they don't have already have it.
    Assumes the text tile is created in at least one dashboard - this will be used to add to additional dashboards. """

    # create empty list of dashboards to remove from list
    dashboard_list_with_text_tile = []

    # check if dashboards already have the text tile
    for dashboard_id in dashboard_list_initial:
        body = sdk.dashboard(str(dashboard_id)).__dict__
        for element in range(0, len(body['dashboard_elements'])):
            if body['dashboard_elements'][element]['type'] == 'text':
                title_text = body['dashboard_elements'][element]['title_text'] or ''
                if title_text == 'ADD_TITLE_HERE' or title_text.startswith('ADD MORE HERE IF NEEDED'):
                    dashboard_list_with_text_tile.append(dashboard_id)
                else:
                    continue

    # remove dashboards that already have the legal disclaimer from final list
    dashboard_list_final = [x for x in dashboard_list_initial if x not in dashboard_list_with_text_tile]

    # Load in dashboard with text tile
    dashboard = sdk.dashboard(dashboard_num)
    body = dashboard.__dict__

    # determine dashboard element index for the text tile
    for i in range(0, len(body['dashboard_elements'])):
        if body['dashboard_elements'][i]['type'] == 'text':
            if body['dashboard_elements'][i]['title_text'] == 'Data Disclaimer':
                element_index = i

    # iterate through final list, adding the text tile to the dashboard
    for dashboard_id in dashboard_list_final:
        body['dashboard_elements'][element_index]['dashboard_id'] = dashboard_id
        text_tile_body = body['dashboard_elements'][element_index]
        if is_dryrun:
            click.echo(f"Updating Dashboard {dashboard_id} to include {text_tile_body}")
        else:
            sdk.create_dashboard_element(text_tile_body)

    click.echo(f"Text tiles were added to the following dashboards: {dashboard_list_final}")


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--prod', is_flag=True, default=False)
@click.option('--dryrun', is_flag=True, default=False)
def add_legal_tile(prod: bool, dryrun: bool) -> None:
    # look id that returns a list of dashboards that meet criteria
    look_id = ''
    # dashboard number that has the sample text tile that will be added to additional dashboards
    dashboard_num = ''

    if prod:
        dashboards = _get_dashboard_list(look_id)
        cont = input(f"Continue updating {len(dashboards)} dashboards? (y/n)")  # nosec
        if cont == "y":
            add_legal_text_tile(
                dashboard_num=dashboard_num,
                dashboard_list_initial=dashboards,
                is_dryrun=dryrun
            )
    else:
        dashboard_list_initial = ['3629', '3631']
        add_legal_text_tile(
            dashboard_num=dashboard_num,
            dashboard_list_initial=dashboard_list_initial,
            is_dryrun=dryrun
        )


@cli.command()
def get_dashboard_list() -> None:
    # look id that returns a list of dashboards that meet criteria
    look_id = '8960'

    click.echo(_get_dashboard_list(look_id))


if __name__ == "__main__":
    cli()
