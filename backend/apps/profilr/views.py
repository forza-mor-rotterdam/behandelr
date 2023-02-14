import copy
from collections import Counter

from apps.auth.backends import authenticate
from apps.auth.decorators import login_required
from apps.profilr.forms import HANDLED_OPTIONS, HandleForm
from apps.profilr.utils import get_filter_options
from apps.services import incident_api_service
from django.conf import settings
from django.core.cache import cache
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from profilr_api_services import MSB_VALID_FILTERS

PAGE_SIZE = 10


def http_404(request):
    return render(
        request,
        "404.html",
    )


def http_500(request):
    return render(
        request,
        "500.html",
    )


def http_response(request):
    return HttpResponse("<h1>Hello HttpResponse</h1>")


def root(request):
    if request.user and request.user.is_authenticated:
        return redirect(reverse("incident_index"))
    return redirect(reverse("login"))


def logout(request):
    incident_api_service.logout()
    request.session.flush()
    return redirect(reverse("root"))


def login(request):
    if request.user and request.user.is_authenticated:
        return redirect(reverse("incident_index"))

    error = None
    if request.POST:
        success, result = authenticate(
            request=request,
            username=request.POST.get("_username"),
            password=request.POST.get("_password"),
        )
        if success:
            return redirect(reverse("incident_index"))
        else:
            error = result
    return render(
        request,
        "login/index.html",
        {
            "last_username": request.POST.get("_username", ""),
            "error": error,
        },
    )


@login_required
def filter(request):
    FILTERS = "filters"
    AFDELINGEN = "afdelingen"
    profile = request.user.profile
    user_token = request.user.token
    if request.POST:
        profile = {
            FILTERS: {f: request.POST.getlist(f, []) for f in MSB_VALID_FILTERS},
        }
        if not profile[FILTERS][AFDELINGEN]:
            profile = {
                FILTERS: {f: [] for f in MSB_VALID_FILTERS},
            }
        profile = request.user.set_profile(profile)

    valid_filters = incident_api_service.validate_filters(profile.get(FILTERS))

    filters = copy.deepcopy(valid_filters)

    filters, departments, categories, areas = get_filter_options(filters, user_token)

    filters_count = len([vv for k, v in filters.items() for vv in v])
    incident_count = 0
    if filters_count > 0:
        incidents = incident_api_service.get_list(
            user_token, data=valid_filters, no_cache=True
        )
        incident_count = len(incidents)

        # START: Experimental: Calculate melding count for each filter
        found_afdelingen = Counter([i.get("afdeling", {}).get("id") for i in incidents])
        # found_onderwerpen = Counter(
        #     [i.get("onderwerp", {}).get("id") for i in incidents]
        # )

        filters[AFDELINGEN] = [
            [o[0], o[1], found_afdelingen.get(o[0])]
            for o in filters.get(AFDELINGEN, [])
        ]
        departments = [
            {
                **d,
                "meldingen_count": found_afdelingen.get(d.get("code"), 0),
            }
            for d in departments
        ]
        # END: Experimental: Calculate melding count for each filter
    return render(
        request,
        "filters/form.html",
        {
            FILTERS: filters,
            "valid_filters": valid_filters,
            "profile": profile,
            "areas": areas,
            "departments": departments,
            "categories": categories,
            "filters_count": filters_count,
            "incident_count": incident_count,
            "foldout_states": request.POST.get("foldout_states", []),
        },
    )


STREET_NAME = "streetName"
DAYS = "days"
DEPARTMENT = "department"
STATUS = "status"

sort_function = {
    STREET_NAME: lambda x: x.get("locatie", {}).get("adres", {}).get("straatNaam"),
    DAYS: lambda x: x.get("werkdagenSindsRegistratie"),
    DEPARTMENT: lambda x: x.get("afdeling", {}).get("omschrijving", {}),
    STATUS: lambda x: x.get("status", {}),
}

sort_options = (
    (f"-{DAYS}", "Oud > nieuw"),
    (f"{DAYS}", "Nieuw > oud"),
    (f"{STREET_NAME}", "Straat (a-z)"),
    (f"-{STREET_NAME}", "Straat (z-a)"),
    (f"{DEPARTMENT}", "Afdeling (a-z)"),
    (f"-{DEPARTMENT}", "Afdeling (z-a)"),
    (f"{STATUS}", "Status (a-z)"),
    (f"-{STATUS}", "Status (z-a)"),
)


@login_required
def incident_list(request):
    profile = request.user.profile
    user_token = request.user.token
    sort_by_with_reverse_session = request.session.get("sort_by", f"-{DAYS}")
    sort_by_with_reverse = request.GET.get("sort-by", sort_by_with_reverse_session)
    request.session["sort_by"] = sort_by_with_reverse

    sort_by = sort_by_with_reverse.lstrip("-")
    sort_reverse = (
        len(sort_by_with_reverse.split("-", 1)) > 1
        and sort_by_with_reverse.split("-", 1)[0] == ""
    )
    valid_filters = incident_api_service.validate_filters(profile.get("filters"))

    filters_count = len([vv for k, v in valid_filters.items() for vv in v])

    selected_order_option = sort_function.get(sort_by, sort_function[DAYS])

    # get incidents if we have filters
    incidents = []
    if filters_count > 0:
        incidents = incident_api_service.get_list(
            user_token, data=valid_filters, no_cache=True
        )
        # incidents_sorted = sorted(incidents, key=selected_order_option )
        incidents_sorted = sorted(
            incidents, key=selected_order_option, reverse=sort_reverse
        )

        # temp: spoed key only available in list items, set cache for it
        for i in incidents_sorted:
            cache_key = f"incident_{i.get('id')}_spoed"
            cache.set(cache_key, bool(i.get("spoed")), 60 * 60 * 24)

    return render(
        request,
        "incident/part_list.html",
        {
            "incidents": incidents_sorted,
            "filters_count": filters_count,
            "filters": valid_filters,
            "sort_by": sort_by_with_reverse,
            "sort_options": sort_options,
        },
    )


@login_required
def incident_detail(request, id):
    profile = request.user.profile
    user_token = request.user.token

    incident = incident_api_service.get_detail(id, user_token)
    categories = incident_api_service.get_onderwerpgroepen(user_token)
    sub_cat_ids = {
        sub_cat.get("id"): cat
        for cat in categories
        for sub_cat in cat.get("onderwerpen")
    }
    incident["groep"] = sub_cat_ids.get(incident.get("onderwerp", {}).get("id"))
    spoed_cache_key = f"incident_{incident.get('id')}_spoed"
    areas = incident_api_service.get_wijken(user_token)

    incident = {
        **incident,
        **{
            "spoed": cache.get(spoed_cache_key, False),
        },
    }

    return render(
        request,
        "incident/detail.html",
        {
            "id": id,
            "incident": incident,
            "groupedSubjects": categories,
            "areas": areas,
            "profile": profile,
            "environment": settings.ENVIRONMENT,
        },
    )


@login_required
def incident_list_item(request, id):
    user_token = request.user.token
    incident = incident_api_service.get_detail(id, user_token)
    spoed_cache_key = f"incident_{incident.get('id')}_spoed"
    incident = {
        **incident,
        **{
            "spoed": cache.get(spoed_cache_key, False),
        },
    }

    return render(
        request,
        "incident/list_item.html",
        {
            "incident": incident,
        },
    )


@login_required
def incident_modal_handle(request, id, handled_type=None):
    if not handled_type:
        return HttpResponse("")
    user_token = request.user.token
    incident = incident_api_service.get_detail(id, user_token)
    form = HandleForm(handled_type=handled_type)
    warnings = []
    errors = []
    messages = []
    form_submitted = False
    is_handled = False

    if request.POST:
        form = HandleForm(request.POST, handled_type=handled_type)
        if form.is_valid():
            choice = form.cleaned_data.get("handle_choice", 1)
            external_text = form.cleaned_data.get("external_text", "")
            internal_text = form.cleaned_data.get("internal_text", "")
            choice_type = {
                x: HANDLED_OPTIONS[x][0] for x in range(len(HANDLED_OPTIONS))
            }.get(int(choice), choice)
            choice_not_handled = {
                x: HANDLED_OPTIONS[x][3] for x in range(len(HANDLED_OPTIONS))
            }.get(int(choice), choice)

            data = {
                "meldingId": incident.get("id"),
                "behandelaar": request.user.name,
                "meldingType": choice_type,
                "afhandelOpmerking": external_text,
                "opmerking": internal_text,
                "straat": incident.get("locatie", {})
                .get("adres", {})
                .get("straatNummer"),
                "huisnummer": incident.get("locatie", {})
                .get("adres", {})
                .get("huisnummer"),
                "plaatsbepaling": incident.get("locatie", {}).get("plaatsbepaling", 0),
                "x": incident.get("locatie", {}).get("x", 0),
                "y": incident.get("locatie", {}).get("y", 0),
            }
            if choice_type == "N":
                data.update(
                    {
                        "redenAfhandelenNiet": choice_not_handled,
                    }
                )

            result = incident_api_service.afhandelen(
                incident.get("id"), user_token, data
            )
            if result.get("warnings"):
                warnings = result.get("warnings")
            if result.get("errors"):
                errors = result.get("errors")
            if result.get("messages"):
                messages = result.get("messages")
            form = None
            form_submitted = True
            is_handled = not warnings and not errors
            warnings or errors
            if not settings.ENABLE_MELDING_AFHANDELEN:
                messages.append(
                    "In deze omgeving kunnen meldingen niet worden afgehanded!"
                )

    return render(
        request,
        "incident/modal_handle.html",
        {
            "incident": incident,
            "handled_type": handled_type,
            "form": form,
            "form_submitted": form_submitted,
            "HANDLED_OPTIONS": HANDLED_OPTIONS,
            "parent_context": {
                "form_submitted": form_submitted,
                "errors": errors,
                "warnings": warnings,
                "messages": messages,
                "handled_type": handled_type,
                "is_handled": is_handled,
            },
        },
    )


@login_required
def incident_mutation_lines(request, id):
    request.user.profile
    user_token = request.user.token

    incident = incident_api_service.get_detail(id, user_token)

    mutation_lines = incident_api_service.get_mutatieregels(id, user_token)

    return render(
        request,
        "incident/mutation_lines.html",
        {
            "id": id,
            "mutationLines": mutation_lines,
            "incident": incident,
        },
    )


@login_required
def image_thumbnail(request, id):
    return image_full(request, id, True)


@login_required
def image_full(request, id, thumbnail=False):
    blob = incident_api_service.get_foto(id, request.user.token, thumbnail)
    return FileResponse(blob)


def config(request):
    return render(
        request,
        "config.html",
    )
