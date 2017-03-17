BOT_NAME = 'webmd'

SPIDER_MODULES = ['webmd.spiders']
NEWSPIDER_MODULE = 'webmd.spiders'

#ROBOTSTXT_OBEY = True

# DOWNLOAD_DELAY = 2.5

# CONCURRENT_REQUESTS = 100

ITEM_PIPELINES = {
    'webmd.pipelines.ValidateItemPipeline': 100, \
    'webmd.pipelines.WriteItemPipeline': 200
}
