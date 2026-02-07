$(document).ready(function() {
    $('#loan_form').bootstrapValidator({
        feedbackIcons: {
            valid: 'glyphicon glyphicon-ok',
            invalid: 'glyphicon glyphicon-remove',
            validating: 'glyphicon glyphicon-refresh'
        }
    }).on('success.form.bv', function(e) {
        $('#success_message').slideDown({ opacity: "show" }, "slow");
        $('#loan_form').data('bootstrapValidator').resetForm();
        e.preventDefault();
        const $form = $(e.target);
        const bv = $form.data('bootstrapValidator');
        $.post($form.attr('action'), $form.serialize(), function(result) {
            console.log(result);
        }, 'json');
    });
});
