from __future__ import absolute_import

import looker_sdk
from looker_sdk.sdk.api31.models import WriteDashboardElement, WriteCreateDashboardFilter, WriteDashboardLayout,\
        WriteDashboardLayoutComponent, WriteDashboard
import click


sdk = looker_sdk.init40()


def _overwrite_existing_dashboard(orig_dashboard_id: str, new_dashboard_id: str, is_dryrun: bool) -> None:
    """ Function that takes a new dashboard, and completely overwrites another (original) dashboard. Used when a new
    dashboard is created to replace an existing dashboard, but using a new Dashboard ID (URL) is not feasible. New
    dashboard will be deleted. """

    click.echo(f"Replacing Dashboard {orig_dashboard_id} with Dashboard {new_dashboard_id}")

    orig_dashboard = sdk.dashboard(orig_dashboard_id)
    new_dashboard = sdk.dashboard(new_dashboard_id)

    # Clear out the original dashboard
    for element in orig_dashboard.dashboard_elements:
        if is_dryrun:
            click.echo(f"Deleting dashboard element {element.id} from Dashboard {orig_dashboard_id}")
        else:
            sdk.delete_dashboard_element(element.id)
            click.echo(f"Original dashboard element with ID {element.id} deleted")

    for dashboard_filter in orig_dashboard.dashboard_filters:
        if is_dryrun:
            click.echo(f"Deleting dashboard filter {dashboard_filter.id} from Dashboard {orig_dashboard_id}")
        else:
            sdk.delete_dashboard_filter(dashboard_filter.id)
            click.echo(f"Original dashboard filter with ID {dashboard_filter.id} deleted")

    # apply filters
    for new_filter in new_dashboard.dashboard_filters:
        write_filter_obj = WriteCreateDashboardFilter(
            dashboard_id=orig_dashboard_id,
            name=new_filter.name,
            title=new_filter.title,
            type=new_filter.type,
            default_value=new_filter.default_value,
            model=new_filter.model,
            explore=new_filter.explore,
            dimension=new_filter.dimension,
            row=new_filter.row,
            listens_to_filters=new_filter.listens_to_filters,
            allow_multiple_values=new_filter.allow_multiple_values,
            required=new_filter.required,
            ui_config=new_filter.ui_config
        )
        if is_dryrun:
            click.echo(f"Updating Dashboard {orig_dashboard_id} to include {write_filter_obj}")
        else:
            newly_created_filter = sdk.create_dashboard_filter(write_filter_obj)
            click.echo(f"New dashboard filter with ID {newly_created_filter.id} applied")

    # apply dashboard elements
    new_element_id_list = []
    for new_element in new_dashboard.dashboard_elements:
        write_element_obj = WriteDashboardElement(
            body_text=new_element.body_text,
            dashboard_id=orig_dashboard_id,
            look=new_element.look,
            look_id=new_element.look_id,
            merge_result_id=new_element.merge_result_id,
            note_display=new_element.note_display,
            note_state=new_element.note_state,
            note_text=new_element.note_text,
            query=new_element.query,
            query_id=new_element.query_id,
            refresh_interval=new_element.refresh_interval,
            result_maker=new_element.result_maker,
            result_maker_id=new_element.result_maker_id,
            subtitle_text=new_element.subtitle_text,
            title=new_element.title,
            title_hidden=new_element.title_hidden,
            title_text=new_element.title_text,
            type=new_element.type
        )
        if is_dryrun:
            click.echo(f"Updating Dashboard {orig_dashboard_id} to include new element with title {new_element.title}")
        else:
            newly_created_element = sdk.create_dashboard_element(write_element_obj)
            new_element_id_list.append(newly_created_element.id)
            click.echo(f"New dashboard element with ID {newly_created_element.id} applied")

    # get updated original dashboard, to get layouts of the newly added elements
    orig_dashboard_updated = sdk.dashboard(orig_dashboard_id)

    new_layout = new_dashboard.dashboard_layouts[0]
    orig_layout = orig_dashboard_updated.dashboard_layouts[0]

    # have to skip for dryrun
    if not is_dryrun:
        # apply dashboard component (tile) layouts
        for i in range(len(new_layout.dashboard_layout_components)):
            new_layout_component = new_layout.dashboard_layout_components[i]
            orig_layout_component = orig_layout.dashboard_layout_components[i]
            write_layout_component_obj = WriteDashboardLayoutComponent(
                dashboard_layout_id=orig_layout.id,
                dashboard_element_id=new_element_id_list[i],
                row=new_layout_component.row,
                column=new_layout_component.column,
                width=new_layout_component.width,
                height=new_layout_component.height
            )
            newly_created_dashboard_layout_component = sdk.update_dashboard_layout_component(
                orig_layout_component.id, write_layout_component_obj)
            click.echo(f"New dashboard layout component with ID {newly_created_dashboard_layout_component.id} applied")
    else:
        click.echo("Applied dashboard component layouts")

    # apply dashboard layout
    write_layout_obj = WriteDashboardLayout(
        dashboard_id=orig_dashboard_id,
        type=new_layout.type,
        active=new_layout.active,
        column_width=new_layout.column_width,
        width=new_layout.width
    )
    if is_dryrun:
        click.echo(f"Updating Dashboard {orig_dashboard_id} to include {write_layout_obj}")
    else:
        newly_created_dashboard_layout = sdk.update_dashboard_layout(orig_layout.id, write_layout_obj)
        click.echo(f"New dashboard layout with ID {newly_created_dashboard_layout.id} applied")

    # soft delete new dashboard
    soft_delete_body = {
        'deleted': 'true'
    }
    if is_dryrun:
        click.echo(f"Deleting Dashboard {new_dashboard_id} with updated body: {soft_delete_body}")
    else:
        sdk.update_dashboard(new_dashboard_id, soft_delete_body)
        click.echo(f"New dashboard with ID {new_dashboard_id} deleted")

    # update dashboard attributes
    write_dashboard_obj = WriteDashboard(
        description=new_dashboard.description,
        hidden=new_dashboard.hidden,
        query_timezone=new_dashboard.query_timezone,
        refresh_interval=new_dashboard.refresh_interval,
        # folder=new_dashboard.folder,
        title=new_dashboard.title,
        preferred_viewer=new_dashboard.preferred_viewer,
        # space=new_dashboard.space,
        alert_sync_with_dashboard_filter_enabled=new_dashboard.alert_sync_with_dashboard_filter_enabled,
        background_color=new_dashboard.background_color,
        crossfilter_enabled=new_dashboard.crossfilter_enabled,
        # deleted=new_dashboard.deleted,
        filters_bar_collapsed=new_dashboard.filters_bar_collapsed,
        load_configuration=new_dashboard.load_configuration,
        lookml_link_id=new_dashboard.lookml_link_id,
        show_filters_bar=new_dashboard.show_filters_bar,
        show_title=new_dashboard.show_title,
        # space_id=new_dashboard.space_id,
        # folder_id=new_dashboard.folder_id,
        text_tile_text_color=new_dashboard.text_tile_text_color,
        tile_background_color=new_dashboard.tile_background_color,
        tile_text_color=new_dashboard.tile_text_color,
        title_color=new_dashboard.title_color,
        appearance=new_dashboard.appearance
    )
    if is_dryrun:
        click.echo(f"Updating Dashboard {orig_dashboard_id} with updated body: {write_dashboard_obj}")
    else:
        sdk.update_dashboard(orig_dashboard_id, write_dashboard_obj)
        click.echo(f"Dashboard with ID {orig_dashboard_id} attributes updated: {write_dashboard_obj}")


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--original_dashboard_id', required=True, type=str)
@click.option('--new_dashboard_id', required=True, type=str)
@click.option('--dryrun', is_flag=True, default=False)
def overwrite_existing_dashboard(original_dashboard_id: str, new_dashboard_id: str, dryrun: bool) -> None:
    _overwrite_existing_dashboard(
        orig_dashboard_id=original_dashboard_id,
        new_dashboard_id=new_dashboard_id,
        is_dryrun=dryrun
    )


if __name__ == "__main__":
    cli()
