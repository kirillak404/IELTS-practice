$(document).ready(function() {
    $('input').on('input', function() {
        $(this).removeClass('is-invalid is-valid');
    });
});