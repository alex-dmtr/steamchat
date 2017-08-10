from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views import View
from django.views.generic import TemplateView
import lib.steamapi as steamapi
from lib.steamapi.enums import PersonaState, LoggedIn

steam = steamapi.steamapi()

def is_steam_auth(request):
    try:
        if not 'steamguard' in request.session or not 'oauth_token' in request.session:
            raise 'Not logged in'
        steamguard = request.session['steamguard']
        token = request.session['oauth_token']
        steam.session.cookies.clear()
        steam.oauth_login(steamguard, token)

        steam.chat.login()

        # also login to chat.
        # if not steam.chat.logged_in == LoggedIn.LoggedIn:
        #     steam.chat.login()

        return True
    except Exception as e:
        return False

class Index(TemplateView):
    template_name = 'index.html'
    login_url = '/login/'

    def get(self, request):
        if not is_steam_auth(request):
            return redirect(self.login_url)

        context = {}

        online_friends = []
        for key in steam.chat.friends:
            friend = steam.chat.friends[key]

            if friend.state == PersonaState.Online:
                online_friends.append({
                    'steam_id': friend.steam_id,
                    'name': friend.name
                })

        context['online_friends'] = online_friends
        return render(template_name=self.template_name,
                      request=request,
                      context=context)

class Login(TemplateView):
    template_name = 'login.html'

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        twofactor = request.POST['twofactor'] if 'twofactor' in request.POST else ''
        steamguard = request.POST['steamguard'] if 'steamguard' in request.POST else ''
        captcha = request.POST['captcha'] if 'captcha' in request.POST else ''

        status = steam.login(username=username,
                             password=password,
                             twofactor=twofactor,
                             steamguard=steamguard,
                             captcha=captcha)
        if status != steamapi.enums.LoginStatus.LoginSuccessful:
            context = {
                'username': username,
                'password': password
            }
            if status == steamapi.enums.LoginStatus.TwoFactor:
                context['twofactor'] = True
            elif status == steamapi.enums.LoginStatus.SteamGuard:
                context['steamguard'] = True
            elif status == steamapi.enums.LoginStatus.Captcha:
                context['captcha'] = True
            else:
                pass
            return render(request, template_name=self.template_name, context=context)
        else:
            request.session['steamguard'] = steam.steamguard
            request.session['oauth_token'] = steam.oauth_token
            request.session['oauth_client_id'] = steam.oauth_client_id

            return redirect('/')


class SendMessage(View):
    def post(self, request):
        if not is_steam_auth(request):
            return redirect(self.login_url)

        friend = request.POST['friend']
        message = request.POST['message']

        steam.chat.send_message(recipient=friend, text=message)

        return HttpResponse(200)