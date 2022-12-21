# This Python script is not intended for production purposes, as API keys are not protected.
# You need to populate the access_key, secret_key and ltc_publickey variables, declared at the end of the file.
# Warning: Funds may be lost, as the withdrawal function does not checksum possible mistakes.

import sys # Passing arguments, ie. actions.
import json # JSON manipulation.
import requests # HTTP requests.
import hashlib, time, hmac, base64, urllib.parse # Signature production, as required by Poloniex API.

class SDK:
# This whole class for signature production has been copied from the Python3 example provided by Poloniex.
# Reference: https://github.com/poloniex/polo-spot-sdk/blob/BRANCH_SANDBOX/signature_demo/signature_python_demo.md

	def __init__(self, access_key, secret_key):
		self.__access_key = access_key
		self.__secret_key = secret_key
		self.__time = int(time.time() * 1000)

	# Producing the signature.
	def __create_sign(self, params, method, path):
		timestamp = self.__time

		if method.upper() == "GET":
			params.update({"signTimestamp": timestamp})
			sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
			encode_params = urllib.parse.urlencode(sorted_params)
			del params["signTimestamp"]
		else:
			requestBody = json.dumps(params)
			encode_params = "requestBody={}&signTimestamp={}".format(
				requestBody, timestamp
			)
			
		sign_params_first = [method.upper(), path, encode_params]
		sign_params_second = "\n".join(sign_params_first)
		sign_params = sign_params_second.encode(encoding="UTF8")
		secret_key = self.__secret_key.encode(encoding="UTF8")
		digest = hmac.new(secret_key, sign_params, digestmod=hashlib.sha256).digest()
		signature = base64.b64encode(digest)
		signature = signature.decode()
		return signature

	# Attaching the signature to the HTTP headers.
	def sign_req(self, host, path, method, params, headers):
		sign = self.__create_sign(params=params, method=method, path=path)
		headers.update(
			{
				"key": self.__access_key,
				"signTimestamp": str(self.__time),
				"signature": sign,
			}
		)

		if method.upper() == "POST":
			host = "{host}{path}".format(host=host, path=path)
			response = requests.post(host, data=json.dumps(params), headers=headers)
			return response.json()

		if method.upper() == "GET":
			params = urllib.parse.urlencode(params)
			if params == "":
				host = "{host}{path}".format(host=host, path=path)
			else:
				host = "{host}{path}?{params}".format(host=host, path=path, params=params)
			response = requests.get(host, params={}, headers=headers)
			return response.json()

		if method.upper() == "PUT":
			host = "{host}{path}".format(host=host, path=path)
			response = requests.put(host, data=json.dumps(params), headers=headers)
			return response.json()

		if method.upper() == "DELETE":
			host = "{host}{path}".format(host=host, path=path)
			response = requests.delete(host, data=json.dumps(params), headers=headers)
			return response.json()


def obtainBalances():
    # This function checks the balances in Poloniex by making an API call. 
    # Reference: https://docs.poloniex.com/#authenticated-endpoints-accounts-all-account-balances
	path_req = "/accounts/balances" # Authenticated API endpoint
	method_req = "get" # HTTP method
	params_req = {"limit": 10} # Limit of results

	# Composing HTTP request.
	res = service.sign_req(
		host,
		path_req,
		method_req,
		params_req,
		headers)

	# Parsing the JSON output so we get the relevant balances.
	balances = res[0]["balances"]
	return balances


def checkBalance():
	# This function will print the balances that we saved from the API call in obtainBalances() function.
	balances = obtainBalances()
	print(balances) # Todo: beautify output
	

def balance(currency):
	# This function aims to isolate the balance of a given currency.

	# Bringing the total balances output to this function.
	balances = obtainBalances()
	
	# Finding the index of relevant currency based on balances list of dictionaries, as the list order may vary
	# based on the user account balances.
	currency_index = [currency in i['currency'] for i in balances].index(True)

	# Once we have the index, we can check the available balance for any given currency.
	currency_balance = balances[currency_index]["available"]
	# Debug: print(currency_balance, currency)

	return currency_balance


def buyLtc():
	# Fetching LTC price.
	# Reference: https://docs.poloniex.com/#public-endpoints-market-data
	res = requests.get("https://api.poloniex.com/markets/LTC_USDT/price").json()

	# Passing the relevant information to a local variable.
	ltc_price = res["price"]

	# Printing the informative output.
	print("Current LTC price is " + ltc_price + " USDT.")

	# Checking USDT balance, as it will determine how many units of a given currency we can convert it to.
	usdt_balance = balance('USDT')

	# Debug: Calculations.
	# print(float(ltc_price) - 0.10)
	print("We can convert our USDT to " + str(round(float(usdt_balance) / (float(ltc_price) - 0.10), 6)) + " units of LTC.")

	# Converting our entire USDT balance to LTC.
	# Reference: https://docs.poloniex.com/#authenticated-endpoints-orders-create-order
	path_req = "/orders" # Authenticated API endpoint
	method_req = "post" # HTTP method
	params_req = {
		"symbol": "ltc_usdt",
		"accountType": "spot",
		"type": "limit",
		"side": "buy",
		"timeInForce": "GTC",
		"price": round(float(ltc_price) - 0.10, 2),
		"quantity": round(float(usdt_balance) / (float(ltc_price)), 6),
		"clientOrderId": "",
	} # We deduct 0.10 to current price in order to set an order below mid-price (maker, lower fees).
	# We round the quantity to 6 decimal places in order to prevent quantity scale error.
	# We also round the price to 2 decimal places in order to prevent price scale error.

	# Assembling the request to the API endpoint.
	res = service.sign_req(
		host,
		path_req,
		method_req,
		params_req,
		headers)

	# Displaying response from API endpoint.
	print(res)


def withdrawLtc():
	# This function allows to withdraw the full LTC balance to a given public key.
	# Warning: In order for this function to work, withdrawal permissions must be given to the API key. Make sure only your authorised IP addresses are whitelisted in the relevant API key. Make sure 2FA is enabled in the account in order to prevent an attacker from modifying the whitelisted IP address list.
	# Reference: https://docs.poloniex.com/#authenticated-endpoints-wallets-withdraw-currency

	# Checking LTC balance, as it will determine how many units of this currency we can withdraw.
	ltc_balance = balance('LTC')

	path_req = "/wallets/withdraw" # Authenticated API endpoint.
	method_req = "post" # HTTP method.
	params_req = {
		"currency": "LTC",
		"amount": ltc_balance,
		"address": ltc_publickey
	} # This will use LTC main chain. For TRC20 chain, replace "LTC" with "LTCTRON".
	# Note: `curl -X GET https://api.poloniex.com/currencies?includeMultiChainCurrencies=true` shows all chains.

	# assembling the request to the API endpoint.
	res = service.sign_req(
		host,
		path_req,
		method_req,
		params_req,
		headers)

	# Displaying response from API endpoint
	print(res)


def depositAddress():
	# This function will retrieve the deposit address for a given currency.
	# It is hardcoded for TRC20 USDT, but the currency can be interchanged with any other supported currency, or even make a more modular on-demand function.
	# Reference: https://docs.poloniex.com/#authenticated-endpoints-wallets-deposit-addresses
	path_req = "/wallets/addresses" # Authenticated API endpoint.
	method_req = "get" # HTTP method.
	params_req = {
		"currency": "USDTTRON"
	} # This will use the TRC20 chain of USDT".
	# Note: `curl -X GET https://api.poloniex.com/currencies?includeMultiChainCurrencies=true` shows all chains.

	# assembling the request to the API endpoint.
	res = service.sign_req(
		host,
		path_req,
		method_req,
		params_req,
		headers)

	# Displaying response from API endpoint
	print(res)




if __name__ == "__main__":
	if len(sys.argv)<2:
		print("Fatal: You forgot to include the relevant action on the command line.")
		print("Usage: python3 %s <action>" % sys.argv[0])
		print("\nAvailable actions: \ncheckBalance \nbuyLtc \nwithdrawLtc \ndepositAddress")
		sys.exit(1)
	headers = {"Content-Type": "application/json"}
	host = "https://api.poloniex.com"
	access_key = ""
	secret_key = ""
	ltc_publickey = ""
	service = SDK(access_key, secret_key)
	globals()[sys.argv[1]]()
	
