import datetime
from django.shortcuts import render

def get_month_info(request, year, month):

    date = datetime.date(year, month, 1)
    days = []

    for spacer in range(int(date.strftime('%w'))):
        days += [None]

    month_away  = datetime.date(year,   month+1, 1) or \
                  datetime.date(year+1, 1,       1)

    month_range = (month_away - date).days

    for day in range(month_range):
        days += [date + datetime.timedelta(days=day)]

    weeks = []
    for week in range(0, len(days), 7):
        weeks += [days[week:week+7]]

    return weeks


def display_month(request, y, m):
    month_as_list = get_month_info(request, int(y), int(m))
    month_name = datetime.date(int(y), int(m), 1).strftime('%B')
    title = f'{month_name} {y}'

    return render(request, 'widgets/cal/month.html', {
            'month': month_as_list,
            'title': title
        })






if __name__ == '__main__':

    info = get_month_info(None, 2023, 6)
    print(info)