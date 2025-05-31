import openai
from django.conf import settings
from django.db.models import Q
from .models import Pessoa

openai.api_key = settings.OPENAI_API_KEY

def get_pessoa_model_fields_info():
    fields_info = {}
    campos_relevantes = ['nome', 'idade', 'cidade', 'email', 'data_cadastro']

    for field in Pessoa._meta.get_fields():
        if field.concrete and field.name in campos_relevantes:
            tipo = field.get_internal_type()
            if 'CharField' in tipo or 'TextField' in tipo:
                tipo_simples = 'String'
            elif 'IntegerField' in tipo:
                tipo_simples = 'Integer'
            elif 'EmailField' in tipo:
                tipo_simples = 'Email (String)'
            elif 'DateField' in tipo:
                tipo_simples = 'Date (YYYY-MM-DD)'
            else:
                tipo_simples = tipo
            fields_info[field.name] = tipo_simples

    return fields_info

def get_llm_prompt(user_query):
    model_fields = get_pessoa_model_fields_info()
    descricao = "\n".join([f"- {name} ({tipo})" for name, tipo in model_fields.items()])

    return f"""
Você é um assistente de IA que traduz linguagem natural para Django ORM.
O modelo 'Pessoa' tem os campos:
{descricao}

Traduza a consulta abaixo para Django ORM, começando com Pessoa.objects.
Não use delete(), update(), create(), raw(), annotate() (exceto Count) ou aggregate() (exceto Count).

Exemplos:
- "Quais são todas as pessoas?" -> Pessoa.objects.all()
- "Pessoas com mais de 30 anos" -> Pessoa.objects.filter(idade__gt=30)
- "Quantas se chamam Maria?" -> Pessoa.objects.filter(nome='Maria').count()

Consulta:
"{user_query}"

Query ORM:
"""

def get_openai_response(prompt_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # ou "gpt-4" se disponível
            messages=[
                {"role": "system", "content": "Você é um tradutor de linguagem natural para Django ORM."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.2,
            max_tokens=150
        )
        result = response.choices[0].message.content.strip()

        if not result.startswith("Pessoa.objects."):
            linhas = [l for l in result.split('\n') if l.strip().startswith("Pessoa.objects.")]
            if linhas:
                return linhas[0].strip()
            raise ValueError("LLM não retornou uma query ORM válida.")
        return result

    except Exception as e:
        print("Erro na API:", e)
        return None

def execute_orm_query(query_str):
    if not query_str.strip().startswith("Pessoa.objects."):
        return "Erro: Query inválida."

    try:
        contexto_seguro = {"__builtins__": __builtins__, "Pessoa": Pessoa, "Q": Q}
        resultado = eval(query_str, contexto_seguro, {"Pessoa": Pessoa, "Q": Q})

        if isinstance(resultado, (int, float, bool)) or resultado is None:
            return resultado
        elif hasattr(resultado, 'all'):
            if resultado.exists() and isinstance(resultado.first(), Pessoa):
                return [f"{p.nome} (Idade: {p.idade}, Cidade: {p.cidade}, Email: {p.email})" for p in resultado]
            return list(resultado)
        elif isinstance(resultado, Pessoa):
            return f"{resultado.nome} (Idade: {resultado.idade}, Cidade: {resultado.cidade}, Email: {resultado.email})"
        return str(resultado)

    except Exception as e:
        return f"Erro ao executar query: {str(e)}"
