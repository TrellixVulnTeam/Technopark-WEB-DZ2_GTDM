from urllib import request

from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.generic import ListView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import Question, Answer, Profile, Tag
from .forms import LoginForm, SignUpForm, ProfileEdit, UserEdit, QuestionForm, AnswerForm

# Create your views here.

PAGINATION_SIZE = 10


def paginator(objects_list, request, per_page=20):
    pages = Paginator(objects_list, PAGINATION_SIZE)
    page_number = request.GET.get('page')
    page = pages.get_page(page_number)

    return pages, page


def make_content(objects_list, request, per_page=20):
    pages, page = paginator(objects_list, request, per_page)

    content = {
        "paginator": pages,
        "page_content": page,
        "tags": Tag.objects.all().values()[:100]
    }

    return content


def login_view(request):
    if request.method == 'GET':
        user_form = LoginForm()
    elif request.method == 'POST':
        user_form = LoginForm(data=request.POST)
        if user_form.is_valid():
            user = authenticate(request, **user_form.cleaned_data)
            if user:
                login(request, user)
                return redirect(reverse('index'))
            else:
                return redirect(reverse('login'))

    return render(request, "login.html", {"form": user_form})


def signup(request):
    if request.method == 'GET':
        user_form = SignUpForm()
    elif request.method == 'POST':
        user_form = SignUpForm(data=request.POST)
        if user_form.is_valid():
            user = User.objects.create_user(username=user_form.cleaned_data['username'],
                                            email=user_form.cleaned_data['email'],
                                            password=user_form.cleaned_data['password'],
                                            )
            user.save()
            profile = Profile.objects.create(user=user)
            profile.save()
            if user:
                login(request, user)
                return redirect(reverse('index'))
            else:
                return redirect(reverse('login'))
    return render(request, "registration.html", {"form": user_form})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def index(request):
    return render(request, "index.html", make_content(Question.objects.all().values(), request))


@login_required(redirect_field_name="login")
def profile(request):
    return render(request, "profile.html", {"tags": Tag.objects.all().values()[:100]})


@login_required(redirect_field_name="login")
def profile_edit(request):
    if request.method == 'GET':
        p_form = ProfileEdit(instance=request.user.profile)
        u_form = UserEdit(instance=request.user)

    elif request.method == 'POST':
        p_form = ProfileEdit(data=request.POST, instance=request.user.profile, files=request.FILES)
        u_form = UserEdit(data=request.POST, instance=request.user)
        if p_form.is_valid() and u_form.is_valid():
            u_form.instance.save()
            p_form.instance.save()
            messages.success(request, f"Your account has been updated!")
            return redirect('profile_edit')
        else:
            messages.success(request, f"Your account has not been updated :(")
            return redirect(reverse('profile_edit'))

    content = {
        "p_form": p_form,
        "u_form": u_form,
        "tags": Tag.objects.all().values()[:100]
    }

    return render(request, "profile_edit.html", content)


# @login_required(redirect_field_name=reverse('login'))
def ask(request):
    if request.method == 'GET':
        form = QuestionForm()
    elif request.method == 'POST':
        form = QuestionForm(data=request.POST)
        if form.is_valid():
            qstn = Question.objects.create(title=form.cleaned_data['title'],
                                           content=form.cleaned_data['content'],
                                           author=request.user.profile)
            qstn.save()
            if qstn:
                messages.success(request, f"Question have been asked!")
                return redirect(reverse("question", args=[qstn.id]))
            else:
                messages.error(request, f"Question have not been created :(")
                return redirect(reverse('ask'))

    content = {
        "form": form,
        "tags": Tag.objects.all().values()[:100]
    }

    return render(request, "ask.html", content)


def answer(request, id: int):
    if request.method == 'GET':
        form = AnswerForm()
    elif request.method == 'POST':
        form = AnswerForm(data=request.POST)
        if form.is_valid():
            answr = Answer.objects.create(question=Question.objects.get_question_by_id(id).get(),
                                          author=request.user.profile,
                                          content=form.cleaned_data['content'],
                                          )
            answr.save()
            if answr:
                messages.success(request, f"Question have been asked!")
                return redirect(reverse("question", args=[answr.question.id]))
            else:
                messages.error(request, f"Question have not been created :(")
                return redirect(reverse('ask'))

    content = {
        "form": form,
        "question_id": id,
        "tags": Tag.objects.all().values()[:100]
    }

    return render(request, "answer_form.html", content)


def question(request, i: int):
    qstn = Question.objects.get_question_by_id(i).values()
    content = make_content(Answer.objects.get_answer_by_question(i), request)
    content["question"] = qstn[0]

    if request.method == 'GET':
        form = AnswerForm()
    elif request.method == 'POST':
        form = AnswerForm(data=request.POST)
        if form.is_valid():
            answr = Answer.objects.create(question_id=qstn[0]['id'],
                                          author=request.user.profile,
                                          content=form.cleaned_data['content'],
                                          )
            answr.save()
            if answr:
                messages.success(request, f"Question have been asked!")
                return redirect(reverse("question", args=[qstn[0]['id']]))
            else:
                messages.error(request, f"Question have not been created :(")
                return redirect(reverse('ask'))

    content["answer_form"] = form

    return render(request, "question_page.html", content)


def tag(request, title: str):
    content = make_content(Question.objects.get_questions_by_tag_title(title).values(), request)
    return render(request, "index.html", content)


def hot(request):
    return render(request, "index.html", make_content(list(Question.objects.get_popular()), request))

def vote(request):
    print(request.GET)
    return JsonResponse({'result_code': 0})