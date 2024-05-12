from itertools import chain

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Post, PostLike, FollowersCount


# Create your views here.
@login_required(login_url='signin')
def index(request):
    user_profile = Profile.objects.get(user=request.user)

    user_following_usernames = []
    feed = []
    feed.append(Post.objects.filter(user=request.user.username))

    user_following = FollowersCount.objects.filter(follower=request.user.username)

    for users in user_following:
        user_following_usernames.append(users.user)
    for username in user_following_usernames:
        feed_list = Post.objects.filter(user=username)
        feed.append(feed_list)


    feed_list = list(chain(*feed))


    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'index.html', {'user_profile': user_profile, 'posts': feed_list})

@login_required(login_url='signin')
def upload(request):
    current_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        user = request.user.username
        profileimg_url = current_profile.profileimg.url
        image = request.FILES.get('image')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption, profileimg_url=profileimg_url)
        new_post.save()
        return redirect('/')
    else:
        return redirect('/')


def post_like(request):
    username = request.user.username
    post_id = request.GET['post_id']
    like_filtered = PostLike.objects.filter(username=username, post_id=post_id).first()

    if like_filtered is None:
        new_like = PostLike.objects.create(username=username, post_id=post_id)
        new_like.save()


        post = Post.objects.get(id=post_id)
        post.no_of_likes += 1
        post.liked = True
        post.save()
    else:
        like_filtered.delete()

        post = Post.objects.get(id=post_id)
        post.no_of_likes -= 1
        post.liked = False
        post.save()
    return redirect('/')


def follow(request):
    follower = request.POST['follower']
    user = request.POST['user']

    if FollowersCount.objects.filter(follower=follower, user=user).first():
        delete_follower = FollowersCount.objects.get(follower=follower, user=user)
        delete_follower.delete()
        return redirect('profile/' + user)

    else:
        new_follower = FollowersCount.objects.create(follower=follower, user=user)
        new_follower.save()
        return redirect('profile/' + user)


def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    posts = Post.objects.filter(user=pk).order_by('-created_at')
    length_of_posts = len(posts)

    user_following = len(FollowersCount.objects.filter(follower=pk))
    user_followers = len(FollowersCount.objects.filter(user=pk))

    if FollowersCount.objects.filter(user=pk, follower=request.user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    context = {
        'user_profile': user_profile,
        'posts': posts,
        'length_of_posts': length_of_posts,
        'user_object': user_object,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following
    }
    return render(request, 'profile.html', context)






@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        if request.FILES.get('image') is None:
            image = user_profile.profileimg
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        if request.FILES.get('image') is not None:
            image = request.FILES['image']
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        return redirect('settings')
    return render(request, 'setting.html', {'user_profile': user_profile})


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already taken...')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username already taken...')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # Log user in and redirect to setting page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                # create a profile object for new user
                user_mode = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_mode, id_user=user_mode.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, 'Password not matching...')
            return redirect('signup')
    else:
        return render(request, 'signup.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid credentials...')
            return redirect('signin')
    else:
        return render(request, 'signin.html')


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('/signin')

