# twitter_sales_bot_v2
Updated Twitter Sales Notification Bot
This version uses the following APIs:
- OpenSea API (need a key)
- LooksRare API (free)
- Etherscan API (free)
- Ethplorer API (free)
- Twitter API (you need elevated access to be able to post images using the v1 auth)

It currently supports sales on OpenSea, LooksRare, and Gem.xyz.

I run it on AWS Lambda using a 5 minute trigger, so the function that sends Tweets is called lambda_handler.

If you want to use it for other contracts, you'll need to change the contracts in lambda_handler and the metadata image link in get_img_url_gem_sweep.
