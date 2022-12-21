from __future__ import absolute_import

import looker_sdk
from looker_sdk import models as ml
import click
from typing import List


sdk = looker_sdk.init40()


PROD_DASH_LIST = []
DEV_DASH_LIST = []

OLD_MODEL = ''
OLD_EXPLORE = ''
NEW_MODEL = ''
NEW_EXPLORE = ''


def _change_dashboard_filters_explore(dashboard_num: str, old_model: str,
                                      old_explore: str, new_model: str, new_explore: str, is_dryrun: bool) -> None:
    """Change the model and/or explore of filters of a dashboard."""
    filters = sdk.dashboard_dashboard_filters(dashboard_num)
    filter_list = []

    for filter_num in range(0, len(filters)):
        if filters[filter_num].model == old_model and filters[filter_num].explore == old_explore:
            filter_id = filters[filter_num].id
            filters[filter_num].model = new_model
            filters[filter_num].explore = new_explore
            if is_dryrun:
                click.echo(f"Updating Dashboard Filter {filter_id} to include {filters[filter_num]}")
            else:
                sdk.update_dashboard_filter(filter_id, filters[filter_num])
            filter_list.append(filter_id)
        else:
            continue
    if len(filters) == 0:
        click.echo("This dashboard does not exist or does not have any filters")
    else:
        click.echo(f"Dashboard ID {dashboard_num}: changed model/explore of {len(filter_list)} filters")


# Assumes view and field names are the same
def _change_dashboard_explore(dashboard_list: List[str], old_model: str,
                              old_explore: str, new_model: str, new_explore: str, is_dryrun: bool) -> None:
    """Change the model and/or explore of tiles and filters on a given list of dashboards."""
    click.echo(f"Changing dashboard list {dashboard_list}")
    for dashboard_num in dashboard_list:
        # change the explore/model of the dashboard filters
        _change_dashboard_filters_explore(
                            dashboard_num=dashboard_num,
                            old_model=old_model,
                            old_explore=old_explore,
                            new_model=new_model,
                            new_explore=new_explore,
                            is_dryrun=is_dryrun
                            )

        tile_counter = 0
        response_dashboard_elements = sdk.dashboard_dashboard_elements(dashboard_num)
        if len(response_dashboard_elements) == 0:
            click.echo("This dashboard does not exist or does not have query tiles")
            continue

        for index in range(0, len(response_dashboard_elements)):
            # Check if it's a non-text tile AND is in target model/explore
            if response_dashboard_elements[index].type != 'text':
                # Look-linked tile - get query id of look
                if 'look_id' in response_dashboard_elements[index]:
                    if (response_dashboard_elements[index].look
                        and response_dashboard_elements[index].look.query.model == old_model
                            and response_dashboard_elements[index].look.query.view == old_explore):
                        query_id = response_dashboard_elements[index].look.query_id
                        look_id = response_dashboard_elements[index].look_id
                    else:
                        continue
                # merged query tile - get query ids & change source query
                elif 'merge_result_id' in response_dashboard_elements[index]:
                    merge_id = response_dashboard_elements[index].merge_result_id
                    merge_query = sdk.merge_query(merge_id)
                    change_tile_flag = 0
                    for source_query in merge_query.source_queries:
                        source_query_id = source_query.query_id
                        query = sdk.query(source_query_id)
                        if (query
                                and query.model == old_model
                                and query.view == old_explore):
                            query_id = query.id
                            change_tile_flag = 1

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
                            source_query['query_id'] = new_query.id

                    # if there are no queries from the target model/explore, skip element
                    if change_tile_flag == 0:
                        continue
                else:
                    # Normal query tile - get query id of tile
                    if (response_dashboard_elements[index].query
                        and response_dashboard_elements[index].query.model == old_model
                            and response_dashboard_elements[index].query.view == old_explore):
                        query_id = response_dashboard_elements[index].query_id
                    else:
                        continue
            # if it's not a query tile, go back to top of loop
            else:
                continue

            element_id = response_dashboard_elements[index].id
            tile_counter += 1
            # Merge queries
            if 'merge_result_id' in response_dashboard_elements[index]:
                # create new merge query body
                merge_query_body = ml.WriteMergeQuery(
                    column_limit=merge_query.column_limit,
                    dynamic_fields=merge_query.dynamic_fields,
                    pivots=merge_query.pivots,
                    sorts=merge_query.sorts,
                    total=merge_query.total,
                    vis_config=merge_query.vis_config,
                    source_queries=merge_query.source_queries
                )

                new_merge_query = sdk.create_merge_query(merge_query_body)
                response_dashboard_elements[index].merge_result_id = new_merge_query.id
                if is_dryrun:
                    click.echo(f"Updating Dashboard Element {element_id} to include new merge result query "
                               f"{response_dashboard_elements[index].merge_result_id}")
                else:
                    sdk.update_dashboard_element(element_id, response_dashboard_elements[index])
            # non-Merge queries
            else:
                # get query response
                query = sdk.query(query_id)

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
                # update query id in dashboard
                if 'look_id' in response_dashboard_elements[index]:
                    response_dashboard_elements[index].look.query_id = new_query.id
                    if is_dryrun:
                        click.echo(f"Updating Look {look_id} to include Explore: {new_query.view}"
                                   f" & Model: {new_query.model}")
                    else:
                        sdk.update_look(look_id, {'query_id': new_query.id})
                else:
                    response_dashboard_elements[index].query_id = new_query.id
                    if is_dryrun:
                        click.echo(f"Updating Dashboard Element {element_id} to include Explore: {new_query.view}"
                                   f" & Model: {new_query.model}")
                    else:
                        sdk.update_dashboard_element(element_id, response_dashboard_elements[index])
        click.echo(f"Dashboard ID {dashboard_num}: changed model/explore of {tile_counter} tiles")


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--prod', is_flag=True, default=False)
@click.option('--dryrun', is_flag=True, default=False)
def change_dashboard_explore(prod: bool, dryrun: bool) -> None:
    dashboard_list = DEV_DASH_LIST
    if prod:
        dashboard_list = PROD_DASH_LIST

    _change_dashboard_explore(
        dashboard_list=dashboard_list,
        old_model=OLD_MODEL,
        old_explore=OLD_EXPLORE,
        new_model=NEW_MODEL,
        new_explore=NEW_EXPLORE,
        is_dryrun=dryrun
    )


if __name__ == "__main__":
    cli()
