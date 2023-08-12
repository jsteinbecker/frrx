from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from frate.models import Schedule, Version


def publish(request, dept, sch, ver):
    """Publish a version of a schedule."""
    schedule = get_object_or_404(Schedule, department=dept, slug=sch)
    version = get_object_or_404(Version, schedule=schedule, n=ver)

    if not version.is_best:
        redirect('dept:sch:ver:publish-suboptimal', dept=dept, sch=sch, ver=ver)

    version.status = version.StatusChoices.PUBLISHED
    version.save()
    schedule.status = schedule.StatusChoices.PUBLISHED
    schedule.save()

    archive_count = 0
    for ver in schedule.versions.exclude(pk=version.pk):
        ver.status = ver.StatusChoices.ARCHIVED
        ver.save()
        archive_count += 1

    messages.success(request,
                     f'Version {version.n} of {schedule.slug} published.'
                            f' {archive_count} previous versions archived.')

    return redirect('dept:sch:detail', dept=dept, sch=sch)


def unpublish(request, dept, sch, ver):
    """Unpublish a version of a schedule."""
    schedule = get_object_or_404(Schedule, department=dept, slug=sch)
    version = get_object_or_404(Version, schedule=schedule, n=ver)

    version.status = version.StatusChoices.DRAFT
    version.save()
    schedule.status = schedule.StatusChoices.DRAFT
    schedule.save()

    messages.success(request,
                     f'Version {version.n} of {schedule.slug} unpublished.')

    return redirect('dept:sch:detail', dept=dept, sch=sch)
