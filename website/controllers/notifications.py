from flask import current_app, render_template_string
from flask_mail import Message, Mail
from threading import Thread
from ..extensions import mail

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipient, template, **kwargs):
    """Send an email asynchronously"""
    msg = Message(
        subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[recipient]
    )
    
    # HTML template for the email
    msg.html = render_template_string("""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">{{ title }}</h2>
            <p>Hello,</p>
            <p>{{ owner_name }} has shared their campsite list "{{ list_name }}" with you.</p>
            <p>You now have permission to view and edit this list.</p>
            <p>To access the list, please visit:</p>
            <p><a href="{{ url }}" style="display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px;">View Shared List</a></p>
            <p>If you didn't expect this invitation, please contact us.</p>
            <p>Best regards,<br>The Campsite Team</p>
        </div>
    """, **kwargs)

    # Create a thread for sending the email
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()

# Observer pattern for notifications
class CollaborationNotifier:
    def notify_new_collaborator(self, owner, collaborator, campsite_list):
        """Send notification when a new collaborator is added"""
        list_url = f"{current_app.config['SITE_URL']}/campsite-lists/{campsite_list.id}"
        
        send_email(
            subject=f"You've been added as a collaborator on a campsite list",
            recipient=collaborator.email,
            template="collaboration_notification.html",
            title="New Campsite List Collaboration",
            owner_name=owner.name,
            list_name=campsite_list.name,
            url=list_url
        )

# Create a global instance
collaboration_notifier = CollaborationNotifier()