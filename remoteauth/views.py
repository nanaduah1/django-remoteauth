import json
from django.http.response import HttpResponse, JsonResponse

from remoteauth import api
from remoteauth.api import ApiResults

API_HANDLER_MAP = dict(
    get=api.fetch,
    post=api.post,
    put=api.put,
    delete=api.delete,
)


def apify(request, path, *args, **kwargs):
    request_method: str = request.method or ""
    api_forwarding_func = API_HANDLER_MAP.get(request_method.lower())
    if not api_forwarding_func:
        return HttpResponse(status=405)

    query_string = request.META.get("QUERY_STRING", "")
    files = request.FILES
    data = request.POST or request.GET
    if not data and request.body:
        data = json.loads(request.body)

    api_result: ApiResults = api_forwarding_func(
        path=f"/{path}/?{query_string}", data=data, files=files
    )

    if api_result.ok:
        return JsonResponse(data=api_result.data)
    else:
        return JsonResponse(
            status=400, data=dict(error=api_result.error_code, **api_result.data)
        )
