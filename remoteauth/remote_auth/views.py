from django.http.response import HttpResponse, JsonResponse

from remote_auth import api
from remote_auth.api import ApiResults

API_HANDLER_MAP = dict(
    get=api.fetch,
    post=api.post,
    put=api.put,
    delete=api.delete,
)


def apify(request, *args, **kwargs):
    request_method:str = request.method or ''
    api_forwarding_func = API_HANDLER_MAP.get(request_method.lower())
    if not api_forwarding_func:
        return HttpResponse(status=405)

    url=request.path
    query_string = request.META.get('QUERY_STRING','')
    files = request.FILES
    data = request.POST or request.GET
    api_result:ApiResults = api_forwarding_func(
        path=f'{url}?{query_string}',
        data=data,
        files=files
    )

    if api_result.ok:
        return JsonResponse(data=api_result.data)
    else:
        return JsonResponse(status=400, data=dict(error=api_result.error_message))
     