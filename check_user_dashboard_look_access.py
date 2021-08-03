
import looker_sdk
import pandas as pd
import os


def get_user_groups(user_id: int, admin_sdk: looker_sdk.sdk.api31.methods.Looker31SDK):
    return admin_sdk.user(user_id).group_ids


def test_user_set_initial_groups(admin_sdk: looker_sdk.sdk.api31.methods.Looker31SDK, test_user: looker_sdk.models.User, real_user: looker_sdk.models.User):
    '''
    Removes all groups from test_user and adds real_user groups
    '''
    body = {
        'user_id': test_user.id
    }
    # Remove all groups from test user
    for group_id in admin_sdk.user(test_user.id).group_ids:
        if group_id != 1:
            admin_sdk.delete_group_user(group_id, test_user.id) # Note that this uses the user.id, not body!

    # Add all groups from real_user to test_user
    for group_id in admin_sdk.user(real_user.id).group_ids:
        if group_id != 1:
            admin_sdk.add_group_user(group_id, body)


def df_from_sdk_all(all_api_endpoint):
    '''
    Generates a pandas DataFrame from a looker_sdk API endpoint
    '''
    all_dict = {}
    for item in all_api_endpoint:
        for key in item.__dict__.keys():
            try:
                all_dict[key]
            # No value in all_dict[key] yet
            except KeyError:
                all_dict[key] = []
            try:
                all_dict[key].append(item[key])
            # No value in item[key]
            except KeyError:
                all_dict[key].append(None)
    
    df = pd.DataFrame(all_dict)
    return df


def get_group_ids(group_df: pd.DataFrame, group_names: list):
    '''
    Returns a list of group_ids from a list of group names
    '''
    return group_df[group_df['name'].isin(group_names)].id.tolist()


def append_or_create_changed_group_content_df(real_user: looker_sdk.models.User, current_group_name: str, orig_df: pd.DataFrame, new_df: pd.DataFrame, changed_content_df: pd.DataFrame, create_new: bool, add_or_remove: str): 
    if add_or_remove == 'remove':
        temp_df_missing = orig_df[~orig_df['id'].isin(new_df['id'])][['id', 'title']]
        temp_df_missing['user_id'] = real_user.id
        temp_df_missing['user_email'] = real_user.email
        temp_df_missing['group_name_changed'] = current_group_name
        temp_df_missing['add_or_remove'] = 'remove'
        temp_df_missing['missing_or_new'] = 'missing'
        temp_df_new = new_df[~new_df['id'].isin(orig_df['id'])][['id', 'title']]
        temp_df_new['user_id'] = real_user.id
        temp_df_new['user_email'] = real_user.email
        temp_df_new['group_name_changed'] = current_group_name
        temp_df_new['add_or_remove'] = 'remove'
        temp_df_new['missing_or_new'] = 'new'
    else:
        temp_df_missing = orig_df[~orig_df['id'].isin(new_df['id'])][['id', 'title']]
        temp_df_missing['user_id'] = real_user.id
        temp_df_missing['user_email'] = real_user.email
        temp_df_missing['group_name_changed'] = current_group_name
        temp_df_missing['add_or_remove'] = 'add'
        temp_df_missing['missing_or_new'] = 'missing'
        temp_df_new = new_df[~new_df['id'].isin(orig_df['id'])][['id', 'title']]
        temp_df_new['user_id'] = real_user.id
        temp_df_new['user_email'] = real_user.email
        temp_df_new['group_name_changed'] = current_group_name
        temp_df_new['add_or_remove'] = 'add'
        temp_df_new['missing_or_new'] = 'new'

    if create_new:
        # changed_content df doesn't exist yet
        changed_content = pd.concat([temp_df_missing, temp_df_new], ignore_index=True)
        changed_content.reset_index()
        return changed_content

    else:
        # Concatenate the temp df to the existing df
        changed_content = pd.concat([changed_content_df, temp_df_missing, temp_df_new], ignore_index=True)
        changed_content.reset_index()
        return changed_content


def check_group_dashboard_look_access(admin_sdk: looker_sdk.sdk.api31.methods.Looker31SDK, group_df: pd.DataFrame, test_user_id: int, user_group_to_test: int, group_names_to_add: list = [], group_names_to_remove: list = []):
    '''
    Checks access for all members of a group, returns df of members whose dashboard / look access has changed along with the dashboards/looks that changed for them. Starting point for debugging.

    user_group_to_test: int - should be an individual integer, iterate through list of group_ids and append df to get all results

    '''
    # Setting variables
    test_user = admin_sdk.user(test_user_id)
    users_in_group = admin_sdk.all_group_users(user_group_to_test)
    
    # Iterate through each user in the current group
    for real_user in users_in_group:
        if real_user.id == 141: # we don't want to include the test_user in this, or it will throw errors
            continue
        else:
            # Extracting group information
            original_groups = get_user_groups(real_user.id, admin_sdk)

        # Remove groups individually from each of these users
        if group_names_to_remove:
            for group_name in group_names_to_remove:

                print('##############################################')
                print(f'Gathering Data from User {real_user.id}')

                # Setting the test_user's groups equal to the real_user's groups
                test_user_set_initial_groups(admin_sdk=admin_sdk, test_user=test_user, real_user=real_user)
                if sorted(admin_sdk.user(test_user_id).group_ids) != sorted(original_groups):
                    raise Exception("The Test User's groups aren't the same as the actual_user's groups")

                # Create the list of group_ids to remove from our test_user
                group_ids_to_remove = get_group_ids(group_df, [group_name])

                # Sudo as the new user (must have API keys set up in 'looker_sudo.ini' folder in same folder as the script)
                if 'looker_sudo.ini' not in os.listdir('.'):
                    raise Exception('Must have looker_sudo.ini file containing API keys in same directory as this script!')

                sdk_sudo = looker_sdk.init31('looker_sudo.ini')

                print('Generating original dashboard and look access')

                # Get all dashboards from user's current group permissions
                dashboard_orig_df = df_from_sdk_all(sdk_sudo.all_dashboards())

                # Get all looks from user's current group permissions
                looks_orig_df = df_from_sdk_all(sdk_sudo.all_looks())

                # body to be used in group assignment
                body = {
                    'user_id': test_user.id
                }

                print(f'Removing group {group_name} from test_user')

                # Deleting deprecated groups (if any)
                if group_ids_to_remove:
                    for group_id in group_ids_to_remove:
                        admin_sdk.delete_group_user(group_id, test_user.id)

                print('Generating new dashboard and look access')

                # Get all dashboards from user's updated group permissions
                dashboard_new_df = df_from_sdk_all(sdk_sudo.all_dashboards())

                # Get all looks from user's updated group permissions
                looks_new_df = df_from_sdk_all(sdk_sudo.all_looks())

                print('------------------RESULTS---------------------')

                # Check that dashboard access is the same
                if list(dashboard_orig_df['id']) == list(dashboard_new_df['id']):
                    print('Dashboard access is the same!')
                else:
                    print('WARNING: Dashboard access is not the same, storing results')
                    try:
                        changed_dashboards = append_or_create_changed_group_content_df(real_user, group_name, dashboard_orig_df, dashboard_new_df, changed_dashboards, create_new=False, add_or_remove='remove')

                    # If we get here, it means that changed_dashboards hasn't been defined yet.
                    except UnboundLocalError:
                        changed_dashboards = append_or_create_changed_group_content_df(real_user, group_name, dashboard_orig_df, dashboard_new_df, changed_content_df=None, create_new=True, add_or_remove='remove')

                # Check that Look access is the same
                if list(looks_orig_df['id']) == list(looks_new_df['id']):
                    print('Look access is the same!')
                else:
                    print('WARNING: Look access is not the same, storing results')
                    try:
                        changed_looks = append_or_create_changed_group_content_df(real_user, group_name, looks_orig_df, looks_new_df, changed_content_df=changed_looks, create_new=False, add_or_remove='remove')
      
                    # If we get here, it means that changed_dashboards hasn't been defined yet.
                    except UnboundLocalError:
                        changed_looks = append_or_create_changed_group_content_df(real_user, group_name, looks_orig_df, looks_new_df, changed_content_df=None, create_new=True, add_or_remove='remove')


        if group_names_to_add:
            for group_name in group_names_to_add:

                # Setting variables
                test_user = admin_sdk.user(test_user_id)
                users_in_group = get_group_ids(group_df, group_names_to_add)

                print('##############################################')
                print(f'Gathering Data from User {real_user.id}')

                # Extracting group information
                original_groups = get_user_groups(real_user.id, admin_sdk)

                # Setting the test_user's groups equal to the real_user's groups
                test_user_set_initial_groups(admin_sdk=admin_sdk, test_user=test_user, real_user=real_user)
                if sorted(admin_sdk.user(test_user_id).group_ids) != sorted(original_groups):
                    raise Exception("The Test User's groups aren't the same as the actual_user's groups")

                # Create the list of group_ids to remove from our test_user
                group_ids_to_add = get_group_ids(group_df, [group_name])

                # Sudo as the new user (must have API keys set up in 'looker_sudo.ini' folder in same folder as the script)
                if 'looker_sudo.ini' not in os.listdir('.'):
                    raise Exception('Must have looker_sudo.ini file containing API keys in same directory as this script!')

                sdk_sudo = looker_sdk.init31('looker_sudo.ini')

                print('Generating original dashboard and look access')

                # Get all dashboards from user's current group permissions
                dashboard_orig_df = df_from_sdk_all(sdk_sudo.all_dashboards())

                # Get all looks from user's current group permissions
                looks_orig_df = df_from_sdk_all(sdk_sudo.all_looks())

                # body to be used in group assignment
                body = {
                    'user_id': test_user.id
                }

                print(f'Adding group {group_name} to test_user')

                # Deleting deprecated groups (if any)
                if group_ids_to_add:
                    for group_id in group_ids_to_add:
                        admin_sdk.add_group_user(group_id, body)

                print('Generating new dashboard and look access')

                # Get all dashboards from user's updated group permissions
                dashboard_new_df = df_from_sdk_all(sdk_sudo.all_dashboards())

                # Get all looks from user's updated group permissions
                looks_new_df = df_from_sdk_all(sdk_sudo.all_looks())

                print('------------------RESULTS---------------------')

                # Check that dashboard access is the same
                if list(dashboard_orig_df['id']) == list(dashboard_new_df['id']):
                    print('Dashboard access is the same!')
                else:
                    print('WARNING: Dashboard access is not the same, storing results')
                    try:
                        changed_dashboards = append_or_create_changed_group_content_df(real_user, group_name, dashboard_orig_df, dashboard_new_df, changed_dashboards, create_new=False, add_or_remove='add')

                    # If we get here, it means that changed_dashboards hasn't been defined yet.
                    except UnboundLocalError:
                        changed_dashboards = append_or_create_changed_group_content_df(real_user, group_name, dashboard_orig_df, dashboard_new_df, changed_content_df=None, create_new=True, add_or_remove='add')

                # Check that Look access is the same
                if list(looks_orig_df['id']) == list(looks_new_df['id']):
                    print('Look access is the same!')
                else:
                    print('WARNING: Look access is not the same, storing results')
                    try:
                        changed_looks = append_or_create_changed_group_content_df(real_user, group_name, looks_orig_df, looks_new_df, changed_content_df=changed_looks, create_new=False, add_or_remove='add')

                    # If we get here, it means that changed_dashboards hasn't been defined yet.
                    except UnboundLocalError:
                        changed_looks = append_or_create_changed_group_content_df(real_user, group_name, looks_orig_df, looks_new_df, changed_content_df=None, create_new=True, add_or_remove='add')

                print('##############################################')

    try:
        changed_dashboards.iloc[0]
    except UnboundLocalError:
        changed_dashboards = 'No Missing Dashboards'

    try:
        changed_looks.iloc[0]
    except UnboundLocalError:
        changed_looks = 'No Missing Looks'

    return changed_dashboards, changed_looks


def create_or_append_changed_user_content_df(real_user: looker_sdk.models.User, orig_df: pd.DataFrame, new_df: pd.DataFrame, changed_content_df: pd.DataFrame, create_new: bool): 
    temp_df_missing = orig_df[~orig_df['id'].isin(new_df['id'])][['id', 'title']]
    temp_df_missing['user_id'] = real_user.id
    temp_df_missing['user_email'] = real_user.email
    temp_df_missing['missing_or_new'] = 'missing'
    temp_df_new = new_df[~new_df['id'].isin(orig_df['id'])][['id', 'title']]
    temp_df_new['user_id'] = real_user.id
    temp_df_new['user_email'] = real_user.email
    temp_df_new['missing_or_new'] = 'new'

    if create_new:
        # changed_content df doesn't exist yet
        changed_content = pd.concat([temp_df_missing, temp_df_new], ignore_index=True)
        changed_content.reset_index()
        return changed_content

    else:
        # Concatenate the temp df to the existing df
        changed_content = pd.concat([changed_content_df, temp_df_missing, temp_df_new], ignore_index=True)
        changed_content.reset_index()
        return changed_content


def check_user_dashboard_look_access(admin_sdk: looker_sdk.sdk.api31.methods.Looker31SDK, group_df: pd.DataFrame, test_user_id: int, actual_user_email: str, group_names_to_add: list = [], group_names_to_remove: list = []):

    # Setting variables
    test_user = admin_sdk.user(test_user_id)
    real_user = admin_sdk.search_users(email=actual_user_email)[0]

    print('##############################################')
    print(f'Gathering Data from User {real_user.id}')

    # Extracting group information
    original_groups = get_user_groups(real_user.id, admin_sdk)

    # Setting the test_user's groups equal to the real_user's groups
    test_user_set_initial_groups(admin_sdk=admin_sdk, test_user=test_user, real_user=real_user)
    if sorted(admin_sdk.user(test_user_id).group_ids) != sorted(original_groups):
        raise Exception("The Test User's groups aren't the same as the actual_user's groups")

    # Create the lists of group_ids to add / remove from our test_user
    group_ids_to_add = get_group_ids(group_df, group_names_to_add)
    group_ids_to_remove = get_group_ids(group_df, group_names_to_remove)

    # Sudo as the new user (must have API keys set up in 'looker_sudo.ini' folder in same folder as the script)
    if 'looker_sudo.ini' not in os.listdir('.'):
        raise Exception('Must have looker_sudo.ini file containing API keys in same directory as this script!')

    sdk_sudo = looker_sdk.init31('looker_sudo.ini')

    print('Generating original dashboard and look access')

    # Get all dashboards from user's current group permissions
    dashboard_orig_df = df_from_sdk_all(sdk_sudo.all_dashboards())

    # Get all looks from user's current group permissions
    looks_orig_df = df_from_sdk_all(sdk_sudo.all_looks())

    # body to be used in group assignment
    body = {
        'user_id': test_user.id
    }

    # Deleting deprecated groups (if any)
    if group_ids_to_remove:
        for group_id in group_ids_to_remove:
            admin_sdk.delete_group_user(group_id, test_user.id)

    # Adding new groups (if any)
    if group_ids_to_add:
        for group_id in group_ids_to_add:
            admin_sdk.add_group_user(group_id, body)

    print('Generating new dashboard and look access')

    # Get all dashboards from user's updated group permissions
    dashboard_new_df = df_from_sdk_all(sdk_sudo.all_dashboards())

    # Get all looks from user's updated group permissions
    looks_new_df = df_from_sdk_all(sdk_sudo.all_looks())

    print('------------------RESULTS---------------------')

    # Check that dashboard access is the same
    if list(dashboard_orig_df['id']) == list(dashboard_new_df['id']):
        print('Dashboard access is the same!')
    else:
        print('WARNING: Dashboard access is not the same, storing results')

        try:
            # if changed_dashboards:
            changed_dashboards = create_or_append_changed_user_content_df(real_user, dashboard_orig_df, dashboard_new_df, changed_dashboards, create_new=False)

        # If we get here, it means that changed_dashboards hasn't been defined yet.
        except UnboundLocalError:
            changed_dashboards = create_or_append_changed_user_content_df(real_user, dashboard_orig_df, dashboard_new_df, changed_content_df=None, create_new=True)

    # Check that Look access is the same
    if list(looks_orig_df['id']) == list(looks_new_df['id']):
        print('Look access is the same!')
    else:
        print('WARNING: Look access is not the same, storing results')
        try:
            changed_looks = create_or_append_changed_user_content_df(real_user, looks_orig_df, looks_new_df, changed_looks, create_new=False)

        # If we get here, it means that changed_dashboards hasn't been defined yet.
        except UnboundLocalError:
            changed_looks = create_or_append_changed_user_content_df(real_user, looks_orig_df, looks_new_df, changed_content_df=None, create_new=True)


    print('##############################################')

    try:
        changed_dashboards.iloc[0]
    except UnboundLocalError:
        changed_dashboards = 'No Missing Dashboards'

    try:
        changed_looks.iloc[0]
    except UnboundLocalError:
        changed_looks = 'No Missing Looks'

    return changed_dashboards, changed_looks
