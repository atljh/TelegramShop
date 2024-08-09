document.addEventListener('DOMContentLoaded', function() {
    const xdayLink = document.querySelector('a[href$="/actions/xday/"]');

    if (xdayLink) {
        xdayLink.addEventListener('click', function(event) {
            event.preventDefault();
            const confirmation = confirm('Вы уверены, что хотите выполнить действие XDay?');

            if (confirmation) {
                const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;

                const form = document.createElement('form');
                form.method = 'POST';
                form.action = xdayLink.href;

                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken;
                form.appendChild(csrfInput);

                document.body.appendChild(form);
                form.submit();
            }
        });
    }
});
