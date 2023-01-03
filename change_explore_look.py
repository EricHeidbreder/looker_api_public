from __future__ import absolute_import

import looker_sdk
from looker_sdk import models as ml
from looker_sdk.error import SDKError
import click
from typing import List


PROD_LOOKS = []
DEV_LOOKS = []
OLD_MODEL = ''
OLD_EXPLORE = ''
NEW_MODEL = ''
NEW_EXPLORE = ''


sdk = looker_sdk.init40()


def _change_look_explore(look_list: List[str], old_model: str, old_explore: str, new_model: str, new_explore: str,
                         is_dryrun: bool) -> None:
    """Change the model and/or explore of a Look"""
    completed_look_list = []
    for look_id in look_list:
        try:
            look = sdk.look(look_id)
            if look.query.model == old_model and look.query.view == old_explore:
                query = look.query

            # create a new query
                new_query_body = ml.WriteQuery(
                    model=new_model,
                    view=new_explore,
                    fields=query.fields,
                    pivots=query.pivots,
                    fill_fields=query.fill_fields,
                    filters=query.filters,
                    filter_expression=query.filter_expression,
                    sorts=query.sorts,
                    limit=query.limit,
                    column_limit=query.column_limit,
                    total=query.total,
                    row_total=query.row_total,
                    subtotals=query.subtotals,
                    vis_config=query.vis_config,
                    filter_config=query.filter_config,
                    visible_ui_sections=query.visible_ui_sections,
                    dynamic_fields=query.dynamic_fields,
                    query_timezone=query.query_timezone
                )
                new_query = sdk.create_query(new_query_body)

                look.query_id = new_query.id
                if is_dryrun:
                    click.echo(f"Updating Look {look_id} to include Explore: {new_query.view}"
                               f" & Model: {new_query.model}")
                else:
                    sdk.update_look(look_id, {'query_id': new_query.id})
                completed_look_list.append(look_id)

            else:
                continue
        except SDKError:
            click.echo(f" Look {look_id} does not exist")
            continue
    click.echo(f"Changed explores of the following Looks: {completed_look_list}")


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--prod', is_flag=True, default=False)
@click.option('--dryrun', is_flag=True, default=False)
def change_look_explore(prod: bool, dryrun: bool) -> None:
    look_list = DEV_LOOKS
    if prod:
        look_list = PROD_LOOKS
    _change_look_explore(
        look_list=look_list,
        old_model=OLD_MODEL,
        old_explore=OLD_EXPLORE,
        new_model=NEW_MODEL,
        new_explore=NEW_EXPLORE,
        is_dryrun=dryrun,
    )


if __name__ == "__main__":
    cli()
