from django.shortcuts import get_object_or_404, redirect, render

from .forms import ImageForm
from .models import Image


def image_upload(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save()
            return redirect('image-detail', pk=image.pk)
    else:
        form = ImageForm()
    return render(request, 'tests/image_form.html', {'form': form})


def image_detail(request, pk):
    image = get_object_or_404(Image, pk=pk)
    return render(request, 'tests/image_detail.html', {'image': image})
