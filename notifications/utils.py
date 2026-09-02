from .models import Notification

def send_notification(user, title, message, type="SYSTEM", link=""):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=type,
        link=link
    )
from .tasks import send_email_task

def send_notification(user, title, message, type="SYSTEM", link="", send_email=False):
    notif = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=type,
        link=link
    )
    if send_email and user.email:
        send_email_task.delay(title, message, [user.email])
    return notif