from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from core.schema import swagger_urlpatterns
from silk import urls as silk_urls


api = [
    path('v1/', include('core.urls.v1')),
]

urlpatterns = [
    path('api/', include(api)),
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),

]
urlpatterns += [
    path('silk/', include(silk_urls, namespace='silk')),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += swagger_urlpatterns
