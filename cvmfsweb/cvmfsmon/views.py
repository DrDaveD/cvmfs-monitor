from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponse
from django.views.decorators.cache import never_cache, cache_page

from cvmfsmon.models import Stratum1

@cache_page(60)
def list(request):
    stratum1s = Stratum1.objects.all().order_by('name')
    return render(request, 'json/list.json')
