from django.shortcuts import render

from ..models import Version


class VersionApiViews:

    @staticmethod
    def version_solving_progress(request, dept, sch, ver):
        version = Version.objects.get(schedule__department_id=dept, schedule__slug=sch, n=ver)
        percent = round(version.slots.filled().count() / version.slots.count() * 100, 2)
        return render(request, 'ver/api/ver-solve-progress.html', {'percent': percent})






