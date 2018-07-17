from django.db import models

# Create your models here.


# 引用django 自带的user表 （需要用到认证 登录功能）
from django.contrib.auth.models import AbstractUser
# 用户表 继承系统表
# 需要 在settings里面修改设置
class UserInfo(AbstractUser):
    """
    用户信息
    """
    nid = models.AutoField(primary_key=True)
    telephone = models.CharField(max_length=11, null=True, unique=True)
    # 注册的时候存放用户的头像
    avatar = models.FileField(upload_to='avatars/', default="avatars/default.png")
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    # 与blog表建立一个一对一的关系
    blog = models.OneToOneField(to='Blog', to_field='nid', null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.username

class Blog(models.Model):
    """
    博客信息
    """
    nid = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name='个人博客标题', max_length=64)
    site_name = models.CharField(verbose_name='站点名称', max_length=64)
    theme = models.CharField(verbose_name='博客主题', max_length=32)

    def __str__(self):
        return self.title


class Category(models.Model):
    """
    博主个人文章分类表
    """
    nid = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name='分类标题', max_length=32)
    # 与博客建立一个一对多的关系 此表 是多
    blog = models.ForeignKey(verbose_name='所属博客', to='Blog', to_field='nid', on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Tag(models.Model):
    # 标签信息表
    nid = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name='标签名称', max_length=32)
    # 一对多的关系 此表 是多
    blog = models.ForeignKey(verbose_name='所属博客', to='Blog', to_field='nid', on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Article(models.Model):
    # 文章表
    nid = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50, verbose_name='文章标题')
    desc = models.CharField(max_length=255, verbose_name='文章描述')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    # 内容
    content = models.TextField()
    # 点赞评论计数
    comment_count = models.IntegerField(default=0)
    up_count = models.IntegerField(default=0)
    down_count = models.IntegerField(default=0)
    # 与用户建立一对多的关系 用户是一 此表是多
    user = models.ForeignKey(verbose_name='作者', to='UserInfo', to_field='nid', on_delete=models.CASCADE)
    # 与分类是一对多的关系 分类表示一  此表是多
    category = models.ForeignKey(to='Category', to_field='nid', null=True, on_delete=models.CASCADE)
    # 与标签表示多对多的关系 此处用through 是不让系统自动建立默认的关系表,从而使用我们自己创建的关系表 方便以后扩展
    tags = models.ManyToManyField(
        to="Tag",
        through='Article2Tag',
    )

    def __str__(self):
        return self.title



# 文章表与 标签表的关系表 (自己创建)
class Article2Tag(models.Model):
    nid = models.AutoField(primary_key=True)
    article = models.ForeignKey(verbose_name='文章', to="Article", to_field='nid', on_delete=models.CASCADE)
    tag = models.ForeignKey(verbose_name='标签', to="Tag", to_field='nid', on_delete=models.CASCADE)

    class Meta:
        unique_together = [
            ('article', 'tag'),
        ]

    def __str__(self):
        v = self.article.title + "---" + self.tag.title
        return v


class ArticleUpDown(models.Model):
    """
    点赞表
    """

    nid = models.AutoField(primary_key=True)
    # 与用户表示一对多的关系 用户是一 此表是多
    user = models.ForeignKey('UserInfo', null=True, on_delete=models.CASCADE)
    # 与文章表示一对多的关系 文章是一 此表是多
    article = models.ForeignKey("Article", null=True, on_delete=models.CASCADE)
    is_up = models.BooleanField(default=True)

    class Meta:
        unique_together = [
            ('article', 'user'),
        ]


class Comment(models.Model):
    """

    评论表

    """
    nid = models.AutoField(primary_key=True)
    # 与文章表建立一对多的关系 文章表示一  此表是多
    article = models.ForeignKey(verbose_name='评论文章', to='Article', to_field='nid', on_delete=models.CASCADE)
    # 与用户表建立一对多的关系 用户表示一  此表是多
    user = models.ForeignKey(verbose_name='评论者', to='UserInfo', to_field='nid', on_delete=models.CASCADE)
    content = models.CharField(verbose_name='评论内容', max_length=255)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    # 此处是找到此评论的父评论,自己关联自己
    parent_comment = models.ForeignKey('Comment', null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.content


















