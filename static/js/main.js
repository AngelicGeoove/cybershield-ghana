function saveDraft() {
    var form = document.querySelector('form');
    if (form) {
        var data = new FormData(form);
        fetch('/report/save-draft', {
            method: 'POST',
            body: data
        }).then(function(r) {
            if (r.redirected) {
                window.location.href = r.url;
            }
        });
    }
}

function confirmDelete() {
    return confirm('Are you sure you want to delete this item?');
}

function togglePassword(fieldId) {
    var field = document.getElementById(fieldId);
    if (field) {
        field.type = field.type === 'password' ? 'text' : 'password';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    var alertElements = document.querySelectorAll('.alert');
    alertElements.forEach(function(el) {
        setTimeout(function() {
            var alert = new bootstrap.Alert(el);
            alert.close();
        }, 5000);
    });
});