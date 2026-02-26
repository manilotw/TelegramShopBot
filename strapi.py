import requests


def get_products(token, product_id=None, base_url=None):
    """Get products from Strapi"""
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{base_url}/api/products'

    if product_id:
        url += f'/{product_id}'
    
    params = {'populate': '*'}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    products = response.json()
    if product_id:
        return products['data']
    return products['data']


def add_product_to_cart(token, cart_id, product_id, quantity, base_url=None):
    """Add product to cart"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "data": {
            "product": product_id,
            "quantity": quantity
        }
    }

    url = f'{base_url}/api/carts/{cart_id}/items'
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']


def get_cart(token, cart_id, base_url=None):
    """Get cart details"""
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{base_url}/api/carts/{cart_id}'
    params = {'populate': '*'}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()['data']


def get_cart_items(token, cart_id, base_url=None):
    """Get items from cart"""
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{base_url}/api/carts/{cart_id}/items'
    params = {'populate': '*'}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()['data']


def remove_cart_item(token, cart_id, item_id, base_url=None):
    """Remove item from cart"""
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{base_url}/api/carts/{cart_id}/items/{item_id}'
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_formatted_cart_items(cart, cart_items):
    """Format cart items for display"""
    items = []
    total = 0
    
    for item in cart_items:
        product = item['attributes']['product']['data']['attributes']
        name = product['name']
        description = product['description']
        quantity = item['attributes']['quantity']
        price = product['price']
        item_total = price * quantity
        total += item_total
        
        items.append(f'{name}: *{quantity}* шт.\n_{description}_\n*{price}₽*')

    items.append(f'\nИтого: *{total}₽*')

    return '\n\n'.join(items)


def get_image_url(token, image_id, base_url=None):
    """Get image URL from Strapi media library"""
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{base_url}/api/upload/files/{image_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    image_url = data['url'] if data['url'].startswith('http') else f'{base_url}{data["url"]}'
    return image_url


def get_product_markdown_output(product):
    """Format product information for display"""
    attributes = product['attributes']
    name = attributes['name']
    description = attributes['description']
    weight = attributes.get('weight', 'N/A')
    price = attributes['price']
    
    output = f'*{name}*\n_{description}_\n{weight} kg\n\n*{price}₽*'
    return output


def create_customer(token, name, email, base_url=None):
    """Create a customer in Strapi"""
    url = f'{base_url}/api/customers'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "data": {
            "name": name,
            "email": email
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']
