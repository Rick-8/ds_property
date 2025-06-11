document.addEventListener("DOMContentLoaded", function () {
  const input = document.querySelector('#id_photo');
  const preview = document.querySelector('#preview-img');
  const previewWrapper = document.querySelector('#image-preview');

  if (input) {
    input.addEventListener('change', function () {
      if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
          preview.src = e.target.result;
          previewWrapper.classList.remove('d-none');
        }
        reader.readAsDataURL(this.files[0]);
      } else {
        previewWrapper.classList.add('d-none');
        preview.src = '';
      }
    });
  }
});
