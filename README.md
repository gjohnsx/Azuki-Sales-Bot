# Azuki Sales Bot by @gjohnsx
<p>Updated Twitter Sales Notification Bot</p>
<img src="https://i.imgur.com/nfyA4C7.png">


## ⚡️ In production
<a href="https://twitter.com/azukisales" target="blank">https://twitter.com/azukisales</a>

## 📝 Notes
This version uses the following APIs:
- OpenSea API (need a key)
- LooksRare API (free)
- Etherscan API (free)
- Ethplorer API (free)
- Twitter API (you need elevated access to be able to post images using the v1 auth)

## 💰 Marketplaces Supported
It currently supports sales on OpenSea, LooksRare, and Gem.xyz.

## 🤖 How It Works
I run it on AWS Lambda using a 5 minute trigger. Every 5 minutes, it gets the Ethereum block number that was mined 5 minutes ago. Then it checks all interactions with a given contract or contracts, and checks if they are a sale and if so, from which marketplace they came.

If you want to use it for other contracts, you'll need to change the contracts in lambda_handler and the metadata image link in get_img_url_gem_sweep.
