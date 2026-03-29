import json
import urllib.request

base = 'http://127.0.0.1:8000/api/v1'
roles = ['admin', 'hr', 'manager', 'employee', 'leadership']


def post(path, payload, headers=None):
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{base}{path}",
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def get(path, headers=None):
    req = urllib.request.Request(f"{base}{path}", headers=headers or {}, method='GET')
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))

for role in roles:
    login = post('/auth/role-login', {'role': role, 'email': f'{role}@acmepms.com', 'name': 'Demo User'})
    token = login['data']['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    if role == 'admin':
        res = get('/admin/dashboard', headers)
        print('admin_total_employees=', res['data']['metrics']['total_employees'])
    elif role == 'hr':
        res = get('/hr/overview', headers)
        print('hr_total_employees=', res['data']['total_employees'])
    elif role == 'manager':
        res = get('/manager/team-performance', headers)
        print('manager_avg_progress=', res['data']['avg_progress'], 'manager_at_risk=', res['data']['at_risk'])
    elif role == 'employee':
        res = get('/employee/dashboard', headers)
        print('employee_progress=', res['data']['progress'], 'checkins=', res['data']['checkins_count'])
    else:
        res = get('/dashboard/overview', headers)
        print('leadership_org_health=', res['data']['kpi']['org_health'])
