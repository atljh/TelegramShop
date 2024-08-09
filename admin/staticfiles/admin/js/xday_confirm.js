document.addEventListener('DOMContentLoaded', function() {
    const xdayButton = document.querySelector('[name="action-button"][value="xday"]');

    if (xdayButton) {
        xdayButton.addEventListener('click', function(event) {
            event.preventDefault();

            if (confirm('Are you sure you want to perform XDay action?')) {
                const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '';

                const hiddenField = document.createElement('input');
                hiddenField.type = 'hidden';
                hiddenField.name = 'csrfmiddlewaretoken';
                hiddenField.value = csrfToken;
                form.appendChild(hiddenField);

                const actionField = document.createElement('input');
                actionField.type = 'hidden';
                actionField.name = 'action';
                actionField.value = 'xday';
                form.appendChild(actionField);

                const applyField = document.createElement('input');
                applyField.type = 'hidden';
                applyField.name = 'apply';
                applyField.value = 'Yes';
                form.appendChild(applyField);

                document.body.appendChild(form);
                form.submit();
            }
        });
    }
});
