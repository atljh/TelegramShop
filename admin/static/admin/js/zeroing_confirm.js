document.addEventListener('DOMContentLoaded', function() {
    const zeroingLink = document.querySelector('a[href$="/actions/zeroing/"]');

    if (zeroingLink) {
        zeroingLink.addEventListener('click', function(event) {
            event.preventDefault();
            const confirmation = confirm('Вы уверены, что хотите выполнить действие Обнуление?');

            if (confirmation) {
                const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;

                const form = document.createElement('form');
                form.method = 'POST';
                form.action = zeroingLink.href;

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
