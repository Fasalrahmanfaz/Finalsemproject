from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
from .models import ChatSession, ChatMessage
from core.ai_engine import generate_chatbot_response


@csrf_exempt
def chatbot_message(request):
    """Main chatbot AJAX endpoint"""
    # Only allow customers (and unauthenticated users) to use chatbot
    if request.user.is_authenticated and getattr(request.user, 'role', '') != 'customer':
        return JsonResponse({'error': 'Chatbot is only available for customers.'}, status=403)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            if not user_message:
                return JsonResponse({'error': 'Empty message'}, status=400)

            # Get or create session
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            user = request.user if request.user.is_authenticated else None
            session, _ = ChatSession.objects.get_or_create(
                session_key=session_key,
                defaults={'user': user}
            )

            # Save user message
            ChatMessage.objects.create(session=session, sender='user', message=user_message)

            # Generate response
            response_text, intent = generate_chatbot_response(user_message, user=user)

            # Save bot response
            ChatMessage.objects.create(session=session, sender='bot', message=response_text, intent=intent)

            return JsonResponse({
                'response': response_text,
                'intent': intent,
                'timestamp': timezone.now().strftime('%H:%M')
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'response': "I'm sorry, I encountered an error. Please try again!", 'intent': 'error'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def chat_history(request):
    """Get chat history for current session"""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'messages': []})

    try:
        session = ChatSession.objects.get(session_key=session_key)
        messages = session.messages.order_by('-created_at')[:30]
        history = [{'sender': m.sender, 'message': m.message, 'time': m.created_at.strftime('%H:%M')} for m in reversed(list(messages))]
        return JsonResponse({'messages': history})
    except ChatSession.DoesNotExist:
        return JsonResponse({'messages': []})
