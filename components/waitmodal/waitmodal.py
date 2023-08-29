from django_components import component



@component.register('WaitModal')
class WaitModal(component.Component):

    template_name = 'components/waitmodal/waitmodal.html'

    def get_context(self, **kwargs):
        id_value = kwargs.get('id_value', None)
        if not id_value:
            id_value = 'waitmodal'

        context = super().get_context(**kwargs)
        context['id_value'] = id_value
        return context



@component.register('WaitModalTrigger')
class WaitModalTrigger(component.Component):

    template_name = 'components/waitmodal/trigger.html'

    def get_context(self, dialog_id=None, **kwargs):
        if dialog_id is None:
            dialog_id = 'waitmodal'

        context = super().get_context(**kwargs)
        context['dialog_id'] = dialog_id
        return context


