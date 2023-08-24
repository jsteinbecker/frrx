from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from frate.models import Schedule, Version


PUBLISH_WITHOUT_VERIFY = 80


def publish_protocol(version: Version):
    schedule = version.schedule

    version.status = version.StatusChoices.PUBLISHED
    version.save()
    schedule.status = schedule.StatusChoices.PUBLISHED
    schedule.save()
    
    archive_count = 0
    for ver in schedule.versions.exclude(pk=version.pk):
        ver.status = ver.StatusChoices.ARCHIVED
        ver.save()
        archive_count += 1

    return f"Version {version.n} of {schedule.slug.upper()} published. {archive_count} previous versions archived."



def publish(request, dept, sch, ver):
    """Publish a version of a schedule."""
    schedule = get_object_or_404(Schedule, department=dept, slug=sch)
    version = get_object_or_404(Version, schedule=schedule, n=ver)

    if not version.is_best:
        return redirect('dept:sch:ver:publish-suboptimal', dept=dept, sch=sch, ver=ver)

    if version.percent < PUBLISH_WITHOUT_VERIFY:
        return redirect('dept:sch:ver:publish-suboptimal', dept=dept, sch=sch, ver=ver)

    publish_message = publish_protocol(version)
    messages.success(request, publish_message)

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
                     f'Version {version.n} of {schedule.slug.upper()} unpublished.')

    return redirect('dept:sch:detail', dept=dept, sch=sch)


def verify_suboptimal_publish(request, dept, sch, ver):
    """
    Verify that the user wants to publish a suboptimal version of a schedule.
    Verification occurs via POST, and will publish the version as is.
    Redirect occurs to the schedule detail page.
    """
    schedule = get_object_or_404(Schedule, department=dept, slug=sch)
    version = get_object_or_404(Version, schedule=schedule, n=ver)

    is_not_best = not version.is_best
    incomplete = version.percent < PUBLISH_WITHOUT_VERIFY

    if request.method == 'POST':
        publish_message = publish_protocol(version)
        messages.success(request, publish_message)
        return redirect('dept:sch:detail', dept=dept, sch=sch)

    context = {
        'schedule': schedule,
        'version': version,
        'is_not_best': is_not_best,
        'incomplete': incomplete,
    }

    return render(request, 'frate/ver/verify_suboptimal_publish.html', context)
