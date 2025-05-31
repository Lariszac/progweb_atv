from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .api import get_llm_prompt, get_openai_response, execute_orm_query

def chat_page(request):
    return render(request, 'chat_app/chat.html')

@csrf_exempt  # Para testes. Em produção, use CSRF token.
def process_query(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message')

            if not user_message:
                return JsonResponse({'error': 'Mensagem vazia.'}, status=400)

            prompt = get_llm_prompt(user_message)
            orm_query = get_openai_response(prompt)

            if not orm_query or "Erro:" in str(orm_query):
                return JsonResponse({'error': 'Erro ao gerar query ORM.', 'orm_query': orm_query or "N/A"})

            result = execute_orm_query(orm_query)

            if isinstance(result, str) and result.startswith("Erro:"):
                return JsonResponse({'error': result, 'orm_query': orm_query})

            return JsonResponse({
                'user_message': user_message,
                'orm_query': orm_query,
                'result': result
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Erro interno: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método não permitido.'}, status=405)
