from django.shortcuts import render,redirect,HttpResponse
from django.contrib import auth
from django.db.models import Avg, Count, Max, Min
from blog.models import Article,UserInfo,Category,Tag,ArticleUpDown,Article2Tag
from blog.models import ArticleUpDown,Comment
import json
from bbs import settings
import os
from utils.code import check_code
from bs4 import BeautifulSoup
from django.http import JsonResponse
from django.db.models import F
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
def code(request):
    img,random_code = check_code()
    request.session['session_name'] =  random_code
    # print(request.session['random_code'])
    from io import BytesIO
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())

# Create your views here.
# 登录
def login(request):
    if request.method=='POST':
        code=request.POST.get('code')
        user=request.POST.get('user')
        pwd=request.POST.get('pwd')
        print(user,pwd)
        session_name = request.session['session_name']
        if code.upper() != session_name.upper():
                return HttpResponse('2')
        user=auth.authenticate(username=user,password=pwd)
        if user:
            auth.login(request,user)
            return HttpResponse('1')
        else:
            return HttpResponse('0')
    return render(request,'login.html')
# 注销
def logout(request):
    auth.logout(request)
    return redirect('/index/')
# 主页显示
def index(request):
    # 所有的文章
    article_list = Article.objects.all()
    # # paginator=Paginator(article_list,2) # 每页显示2条
    # paginator = Paginator(article_list, 5)
    # # 从前端获取当前的页码数,默认为1
    # page = request.GET.get('page', 1)
    # # 把当前的页码数转换成整数类型
    # currentPage = int(page)
    # try:
    #     book_list = paginator.page(page)  # 获取当前页码的记录
    # except PageNotAnInteger:
    #     book_list = paginator.page(1)  # 如果用户输入的页码不是整数时,显示第1页的内容
    # except EmptyPage:
    #     book_list = paginator.page(paginator.num_pages)  # 如果用户输入的页数不在系统的页码列表中时,显示最后一页的内容
    return render(request,'index.html',locals())
# 个人站点
def homesite(request,username,**kwargs):
    user = UserInfo.objects.filter(username=username).first()
    if not user:
        return render(request, "not_found.html")
    # 查询当前站点对象
    blog = user.blog
    # 查询当前用户发布的所有文章
    if not kwargs:
        article_list = Article.objects.filter(user__username=username)

    else:
        condition = kwargs.get("condition")
        params = kwargs.get("params")

        if condition == "category":
            article_list = Article.objects.filter(user__username=username).filter(category__title=params)
        elif condition == "tag":
            article_list = Article.objects.filter(user__username=username).filter(tags__title=params)
        else:
            year, month = params.split("/")
            article_list1 = Article.objects.filter(user__username=username).filter(create_time__month=month)
            article_list = Article.objects.filter(user__username=username).filter(create_time__year=year,
                                                                                  create_time__month=month)
    if not article_list:
        return render(request, "not_found.html")
    cate_list=Category.objects.filter(blog=blog).annotate(c=Count("article__title")).values_list("title", "c")
    tag_list = Tag.objects.filter(blog=blog).annotate(c=Count("article__title")).values_list("title", "c")
    date_list=Article.objects.filter(user=user).extra(select={"y_m_date":"strftime('%%Y/%%m',create_time)"}).values("y_m_date").annotate(c=Count("title")).values_list("y_m_date","c")

    return  render(request,'homesite.html',locals())
# 文章详情页
def articles(request,username,article_id):
    user = UserInfo.objects.filter(username=username).first()
    blog = user.blog
    article_list = Article.objects.filter(nid=article_id).first()
    article_list1 = Article.objects.filter(nid=article_id).values_list("category__title")
    tag_list=Article.objects.filter(nid=article_id).values_list("tags__title")
    comment_list = Comment.objects.filter(article_id=article_id).all()
    return render(request,'aiticles.html',locals())
# 点赞反对
def digg(request):
    print(request.POST)
    is_up=json.loads(request.POST.get("is_up"))
    print(is_up)
    article_id=request.POST.get("article_id")
    user_id=request.user.pk
    response={"state":True,"msg":None}

    obj=ArticleUpDown.objects.filter(user_id=user_id,article_id=article_id).first()
    if obj:
        response["state"]=False
        response["handled"]=obj.is_up
    else:
        with transaction.atomic():
            new_obj=ArticleUpDown.objects.create(user_id=user_id,article_id=article_id,is_up=is_up)
            if is_up:
                Article.objects.filter(pk=article_id).update(up_count=F("up_count")+1)
            else:
                Article.objects.filter(pk=article_id).update(down_count=F("down_count")+1)
    return JsonResponse(response)
# 评论
def comment(request):
    if request.method=='POST':
        print(111)
        pid=request.POST.get('pid')
        user=request.user
        content=request.POST.get('content')
        article_id=request.POST.get('article_id')
        comment_list=Comment.objects.create(content=content,article_id=article_id,parent_comment_id=pid,user=user)
        Article.objects.filter(pk=article_id).update(comment_count=F("comment_count") + 1)
        list={}
        list['content']=content
        list['username']=user.username
        list['pid']=pid
        # json 序列化是有要求的所以需要将时间转为字符串
        list['time']=comment_list.create_time.strftime("%Y-%m-%d %X")
        return JsonResponse(list)
    return HttpResponse('ok')
# 个人管理界面
def backstage(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    user=request.user
    blog = user.blog
    article_lis=Article.objects.filter(user=user).all()
    cate_list = Category.objects.filter(blog=blog).annotate(c=Count("article__title")).values_list("title", "c")
    return render(request,'backstage.html',locals())

# 添加文章
def addarticles(request):
    user = request.user
    # blog = user.blog
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        user = request.user
        cate_pk = request.POST.get("cate")
        tags_pk_list = request.POST.getlist("tags")
        soup = BeautifulSoup(content, "html.parser")
        # print(title,content,user,cate_pk,tags_pk_list)
        # # 文章过滤：
        for tag in soup.find_all():
            # print(tag.name)
            if tag.name in ["script", ]:
                tag.decompose()
        # # 切片文章文本
        desc = soup.text[0:150]
        article_obj = Article.objects.create(title=title, content=str(soup), user=user, category_id=cate_pk, desc=desc)
        for tag_pk in tags_pk_list:
            Article2Tag.objects.create(article_id=article_obj.pk, tag_id=tag_pk)
        return redirect("/backstage/")
    else:

        blog = user.blog
        cate_list = Category.objects.filter(blog=blog).annotate(c=Count("article__title")).values_list("title", "c")
        cate_list1 = Category.objects.filter(blog=blog)
        tags = Tag.objects.filter(blog=blog)
        return render(request, "addarticles.html", locals())
# 用户上传图片
def upload(request):
    print(request.FILES)
    obj=request.FILES.get("upload_img")
    name=obj.name
    path=os.path.join(settings.BASE_DIR,"static","upload",name)
    print(path)
    with open(path,"wb") as f:
        for line in obj:
            f.write(line)
    res={
        "error":0,
        "url":"/static/upload/"+name
    }
    return HttpResponse(json.dumps(res))
# 删除文章
def delarticle(request):
    idd = str(request.GET.get('idd'))
    Article.objects.filter(nid=idd).delete()
    return HttpResponse('ok')
# 修改文章
def update_article(request,id):
    user = request.user
    blog = user.blog
    cate_list = Category.objects.filter(blog=blog).annotate(c=Count("article__title")).values_list("title", "c")
    cate_list1 = Category.objects.filter(blog=blog)
    tags = Tag.objects.filter(blog=blog)
    article_obj=Article.objects.filter(nid=id).first()
    tagss=article_obj.tags.all()
    cat=article_obj.category.title
    taga=[]
    for obj  in tagss:
        taga.append(obj.title)
    if request.method=='POST':
        title = request.POST.get("title")
        content = request.POST.get("content")
        user = request.user
        cate_pk = request.POST.get("cate")
        tags_pk_list = request.POST.getlist("tags")
        soup = BeautifulSoup(content, "html.parser")
        # print(title, content, user, cate_pk, tags_pk_list)
        # # 文章过滤：
        for tag in soup.find_all():
            # print(tag.name)
            if tag.name in ["script", ]:
                tag.decompose()
        # # 切片文章文本
        desc = soup.text[0:150]
        Article.objects.filter(nid=id).update(title=title, content=str(soup), user=user, category_id=cate_pk, desc=desc)
        if Article2Tag.objects.filter(article_id=id):
            Article2Tag.objects.filter(article_id=id).delete()
        for tag_pk in tags_pk_list:
            print(tag_pk)
            Article2Tag.objects.create(article_id=id, tag_id=tag_pk)
        return redirect("/backstage/")
    return render(request,'update_article.html',locals())