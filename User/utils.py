from django.contrib.auth.models import Group, Permission


def create_default_group():
    group_names = ['Super Admin', 'Admin', 'Account', 'Customer Support', 'Account Officer', 'Affiliate Admin',
                   'Manager', 'Sub Agent', 'User']
    for group_name in group_names:
        if not Group.objects.filter(name=group_name).exists():
            Group.objects.create(name=group_name)
    # set_id = []
    # permission_data = Permission.objects.filter(name__contains="Business")
    # for permission in permission_data:
    #     # set_id.append(permission.id)
    #     print(permission.name)
