import looker_sdk
import click
from typing import List
import json


sdk = looker_sdk.init40()


def _get_user_list(look_id: int) -> List[int]:
    """Get a list of users from a look."""
    look_data = sdk.run_look(look_id=look_id, result_format="json", apply_vis=True)
    return [v for d in json.loads(look_data) for k, v in d.items() if k == "ID"]


def _disable_inactive_users(user_id_list: List[int], is_dry_run: bool) -> None:
    """Disable users given a list of User IDs."""
    for user_id in user_id_list:
        user = sdk.user(user_id=str(user_id))
        user.is_disabled = True
        if is_dry_run:
            click.echo(f"Disabled {user.email} with ID {str(user.id)} (Dry Run)")
        else:
            sdk.update_user(user_id=user.id, body=user)
            click.echo(f"Disabled {user.email} with ID {str(user.id)}")


@click.group()
@click.option('--prod', is_flag=True, default=False, help='Run against prod (not dev) inputs.')
@click.option('--dry-run', is_flag=True, default=False,
              help='Run a dry run to test. Will not change anything in Looker.')
@click.pass_context
def cli(ctx, prod, dry_run) -> None:
    ctx.ensure_object(dict)
    ctx.obj['prod'] = prod
    ctx.obj['dry_run'] = dry_run


DEV_USER_ID_LIST = ['869', '1001']
LOOK_ID = '10284'


@cli.command()
@click.pass_context
def disable_inactive_users(ctx) -> None:
    """Disable users given a list of User IDs. When running prod option,
    pulls from a Look identifying users that have been inactive for 180 days."""
    print(f"this is prod: {ctx.obj['prod']}")
    print(f"this is a dry run: {ctx.obj['dry_run']}")
    user_id_list = DEV_USER_ID_LIST
    if ctx.obj['prod']:
        user_id_list = _get_user_list(look_id=LOOK_ID)
    _disable_inactive_users(
        user_id_list=user_id_list,
        is_dry_run=ctx.obj['dry_run']
    )


@cli.command()
def get_user_list() -> None:
    """Returns a list of users that have been inactive for the last 180 days.
    dry-run/prod options do not apply."""
    click.echo(_get_user_list(look_id=LOOK_ID))


if __name__ == "__main__":
    cli()
