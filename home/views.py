from django.shortcuts import get_object_or_404, redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import ListView, FormView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Count
from django.contrib import messages
# from home.forms import CommentForm
from .models import Post  # , Comment


class PostListView(ListView):
    model = Post
    template_name = 'home/home.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        return Post.objects.filter(is_approved=True).order_by('-date_posted')

    def get_context_data(self, **kwargs):
        context = super(PostListView, self).get_context_data(**kwargs)
        # context['most_commented_posts'] = Post.approved.annotate(count=Count('comments')).order_by('-count')[:7]
        return context


class PostSearchView(ListView):
    model = Post
    template_name = 'home/search.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        query = self.request.GET['search']
        if query:
            return Post.approved.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(author__username__icontains=query)).distinct().order_by('-date_posted')
        return Post.approved.all().order_by('-date_posted')


class PostByAuthorView(ListView):
    model = Post
    template_name = 'home/post_by_author.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        author = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.approved.filter(author=author).order_by('-date_posted')


class PostByDateView(ListView):
    model = Post
    template_name = 'home/post_by_date.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        return Post.approved.filter(date_posted__year=year, date_posted__month=month).order_by('-date_posted')


class PostDetailView(DetailView, FormView):
    model = Post
    template_name = 'home/post_detail.html'
    context_object_name = 'post'
    # form_class = CommentForm

    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)
        # context['comments'] = Comment.objects.filter(post=self.object)
        return context

    def form_valid(self, form):
        if self.request.user.is_active:
            # parent_id = form.cleaned_data.get('parent')
            # if parent_id:
            #     parent = get_object_or_404(Comment, id=parent_id.id)  # fetching twice for some more secureuit
            #     form.instance.parent = parent
            # form.instance.post = get_object_or_404(Post, slug=self.kwargs.get('slug'))
            # form.instance.user = self.request.user
            # form.save()
            return redirect(reverse('post-detail', kwargs={"slug": self.kwargs['slug']}))
        else:
            return redirect('login')


class PostCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'slug', 'image', 'content']
    success_message = "Your Post is Created successfully, it will be added to Homepage after approval"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(PostCreateView, self).get_context_data(**kwargs)
        context['page_name'] = "Create Post"
        return context


class PostUpdateView(SuccessMessageMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'slug', 'image', 'content']
    success_message = "Your Post is Updated successfully, it will be added to Homepage after approval"

    def form_valid(self, form):
        form.instance.is_approved = False
        return super().form_valid(form)

    def test_func(self):  # will return true if current user is post's author or current user is admin
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super(PostUpdateView, self).get_context_data(**kwargs)

        context['page_name'] = "Update Post"
        if self.object.image:  # Checking if image exists
            context['image'] = self.object.image.url
        else:
            context['image'] = ""
        return context


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('home')
    success_message = "Your Post is Deleted successfully"

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, self.success_message)
        return super(PostDeleteView, self).delete(request, *args, **kwargs)

    def test_func(self):  # will return true if current user is post's author or current user is admin
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff


# class CommentDeleteView(UserPassesTestMixin, DeleteView):
#     model = Comment

#     def get_success_url(self):
#         post_slug = Comment.objects.get(id=self.kwargs['pk']).post.slug  # fetch post pk from comments pk
#         return reverse_lazy('post-detail', kwargs={"slug": post_slug})

#     def test_func(self):
#         user = Comment.objects.get(id=self.kwargs['pk']).user
#         return self.request.user == user or self.request.user.is_staff
