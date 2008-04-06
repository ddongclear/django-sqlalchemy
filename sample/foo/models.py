import datetime
from django_sqlalchemy import models
from sqlalchemy.orm import relation

# Create your models here.
class Category(models.Model):
    """Category Class"""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    
    def __unicode__(self):
        return self.name
    
class Post(models.Model):
    pub_date = models.DateTimeField(default=datetime.datetime.now)
    title = models.CharField(max_length=100)
    slug = models.SlugField()
    category = models.ForeignKey(Category)
    body = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.body
