from flask import Blueprint, request, jsonify, send_file
from .models import obj_table, media
import instagrapi
import requests
from . import db
import os
import zipfile
import time
from collections import defaultdict
from threading import Lock
from json import JSONDecodeError

# Rate limiting implementation
request_history = defaultdict(list)
rate_limit_lock = Lock()
RATE_LIMIT_WINDOW = 60  # 1 minute window
RATE_LIMIT_MAX_REQUESTS = 30  # Max 30 requests per minute per IP

def is_rate_limited(ip_address):
    """Check if an IP address has exceeded the rate limit."""
    with rate_limit_lock:
        now = time.time()
        # Clean old requests outside the window
        request_history[ip_address] = [req_time for req_time in request_history[ip_address]
                                      if now - req_time < RATE_LIMIT_WINDOW]

        # Check if at limit
        if len(request_history[ip_address]) >= RATE_LIMIT_MAX_REQUESTS:
            return True

        # Add current request
        request_history[ip_address].append(now)
        return False

def get_rate_limit_headers(ip_address):
    """Get rate limit headers for the response."""
    with rate_limit_lock:
        now = time.time()
        # Clean old requests
        request_history[ip_address] = [req_time for req_time in request_history[ip_address]
                                      if now - req_time < RATE_LIMIT_WINDOW]

        remaining = max(0, RATE_LIMIT_MAX_REQUESTS - len(request_history[ip_address]))
        reset_time = int(now + RATE_LIMIT_WINDOW) if request_history[ip_address] else int(now + RATE_LIMIT_WINDOW)

        return {
            'X-RateLimit-Limit': str(RATE_LIMIT_MAX_REQUESTS),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset_time)
        }

download_path = os.path.join(os.getcwd(), 'downloads')

class dInstagram():
    def __init__(self, postUrl, username=None, password=None):
        self.username=username
        self.insta=instagrapi.Client()
        # Set device settings to mimic a real mobile device to avoid Instagram bot detection
        try:
            self.insta.set_device_settings({
                "app_version": "67.0.0.21.97",
                "android_version": 26,
                "android_release": "8.0.0",
                "dpi": "640dpi",
                "resolution": "1440x2560",
                "manufacturer": "OnePlus",
                "device": "ONEPLUS A6000",
                "model": "ONEPLUS A6000",
                "cpu": "qcom",
                "version_code": "1032504608",
                # Additional device identifiers to look more legitimate
                "uuid": "6358432f-0d49-4b6a-9439-035a6ee7db2e",
                "phone_id": "ze22eks0QGwxbqtZr0qoUgAaIVBdoGvNWCpBlQeM",
                "advertising_id": "6358432f-0d49-4b6a-9439-035a6ee7db2e"
            })
            # Set uptime to a reasonable value (device has been on for some time)
            self.insta.set_uptime(86400)  # 1 day in seconds
        except Exception:
            # If device settings fail, continue with default settings
            pass
        # Set common headers to make requests look more like a regular browser
        try:
            self.insta.set_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "*/*",
                "Referer": "https://www.instagram.com/",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "TE": "trailers"
            })
        except Exception:
            pass
        # Warm up session by making initial request to establish cookies
        try:
            self.insta.get("https://www.instagram.com/")
        except Exception:
            # If warm-up fails, continue anyway
            pass
        self.password=password
        self.postUrl=postUrl
        self.id=None

    def getContentType(self, url):
        res=requests.get(url)
        if res.content:
            return [True, res.headers['Content-Type']]
        else:
            return [False, res.status_code]

    def login(self, username, password):
        try:
            self.username=username
            self.password=password
            self.insta.login(self.username, self.password)
            return [True, None]
        except Exception as e:
            print(e)
            return [False, e]

    def getId(self):
        try:
            self.id=self.insta.media_pk_from_url(self.postUrl)
            return [True, self.id]
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return [False, e]
        except Exception as e:
            print("Unexpected error:", e)
            return [False, e]

    def getResources(self):
        def serialize_resource(resource):
            return resource.json()
        try:
            status, id = self.getId()
            if(status):
                resources=self.insta.media_info(id).resources
                res = [serialize_resource(resource) for resource in resources]
                return [True, res]
            else:
                raise Exception("Setting of the resource id failed.")
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return [False, e]
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return [False, e]

    def mediaType(self):
        try:
            status, id = self.getId()
            if(status):
                mtype=self.insta.media_info(id).media_type
                if mtype==1:
                    return [True, "Photo"]
                elif mtype==2:
                    if self.insta.media_info(id).product_type=="feed":
                        return [True, "Video"]
                    elif self.insta.media_info(id).product_type=="igtv":
                        return [True, "IGTV"]
                    elif self.insta.media_info(id).product_type=="clips":
                        return [True, "Clips"]
                elif mtype==8:
                    return [True, "Album"]
            else:
                raise Exception("Failed to set the resource id.")
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return [False, e]
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return [False, e]

    def save(self, url, id):
        try:
            status, contentType=self.getContentType(url)
            if(status):
                filename=self.insta.media_info(id).id+'.'+contentType.split('/')[1]
                filepath=download_path
                full_path = os.path.join(filepath, filename)
                print("filepath ye ra:{}".format(full_path))
                res=requests.get(url)
                with open(full_path, "wb") as f:
                    f.write(res.content)
                med = media(media_path=full_path, resource_id=id, rtype=self.mediaType()[1])
                db.session.add(med)
                db.session.commit()
                return [True, full_path]
            else:
                raise Exception("URL is not valid or doesn't contain a file.")
        except Exception as e:
            print(e)
            return [False, e]

    #main
    def download(self):
        try:
            status, type=self.mediaType()
            res=None
            if(status):
                if type=="Photo":
                    url=self.insta.media_info(self.id).thumbnail_url
                    status2, res= self.save(url, self.id)
                    if(status2):
                        print("Download photo success!")
                    else:
                        print("Download failed.")
                        raise Exception("Download failed.")
                elif type=="Video":
                    url=self.insta.media_info(self.id).video_url
                    status2, res= self.save(url, self.id)
                    if(status2):
                        print("Download video success!")
                    else:
                        print("Download failed.")
                        raise Exception("Download failed.")
                elif type=="Album":
                    status, resources=self.getResources()
                    print(resources[0])
                    print("ye ra type:{}".format(type(resources[0])))
                    if(status):
                        res=[]
                        for r in resources:
                            url=r.thumbnail_url
                            id=r.pk
                            status2, tmp= self.save(url, id)
                            if(status2):
                                res.append(tmp)
                                print("Url: "+url+" saved.")
                            else:
                                print("Url: "+url+" not saved.")
                        if(len(res)!=len(resources) and len(res)>0):
                            print("Not all files in Album are downloaded.")
                        else:
                            raise Exception("Not all files in Album are downloaded.")
                        zip_file_path = os.path.join(download_path, 'download{}.zip'.format(self.id))
                        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                            for file_path in res:
                                # Get only the filename from the file_path
                                file_name = os.path.basename(file_path)
                                # Add the file to the ZIP file without any directory structure
                                zipf.write(file_path, arcname=file_name)
                        res=zip_file_path
                    else:
                        raise Exception("No resources found in the album.")
                elif type=="Clips":
                    url=self.insta.media_info(self.id).video_url
                    status2, res= self.save(url, self.id)
                    if(status2):
                        print("Download clips success!")
                    else:
                        print("Download failed.")
                        raise Exception("Download failed.")
                    print(res)
                return [True, res]
            else:
                raise Exception("Failed to load the type of the resource.")
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return [False, e]
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return [False, e]


insta_views = Blueprint('insta_views', __name__)

@insta_views.route('/', methods=['POST'])
def create_obj():
    try:
        url = request.form.get('url')
        obj = obj_table.query.filter_by(url=url).first()
        if obj:
            return jsonify({'messages': 'Object already present in db.', "id": obj.id})
        obj = obj_table(url=url)
        if request.form.get('username', 0):
            obj.username = request.form.get('username')
        if request.form.get('password', 0):
            obj.password = request.form.get('password')
        db.session.add(obj)
        db.session.commit()
        return jsonify({"messages": "Initialized state of the object.", "id": obj.id})
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@insta_views.route('/login/<int:id>', methods=['PATCH'])
def login(id):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"messages": "Object not found"}), 404

        ins = dInstagram(postUrl=obj.url)
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return jsonify({"messages": "Username and password are required"}), 400

        status, res = ins.login(username=username, password=password)
        if not status:
            # Check if it's a specific Instagram error
            if isinstance(res, instagrapi.exceptions.BadPasswordError):
                return jsonify({"messages": "Invalid password. Please check your credentials."}), 401
            elif isinstance(res, instagrapi.exceptions.UserNotFound):
                return jsonify({"messages": "User not found. Please check your username."}), 401
            elif isinstance(res, instagrapi.exceptions.LoginRequired):
                return jsonify({"messages": "Login required. Please check your credentials."}), 401
            else:
                return jsonify({"messages": f"Login failed: {str(res)}"}), 401

        obj.username = username
        obj.password = password
        db.session.commit()
        return jsonify({"messages": "Login successful.", "user_id": obj.id}), 200
    except Exception as e:
        return jsonify({"messages": f"Login error: {str(e)}"}), 500

@insta_views.route('/<int:id>/resources', methods=['GET'])
def getResources(id):
    try:
        obj = obj_table.query.get(id)
        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)
        status, res = ins.getResources()
        if status:
            return jsonify(res), 200
        else:
            return jsonify({"messages": str(res)}), 500
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@insta_views.route('/<int:id>/getmediatype', methods=['GET'])
def getMediaType(id):
    try:
        obj = obj_table.query.get(id)
        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)
        status, res = ins.mediaType()
        if status:
            return jsonify(res), 200
        else:
            return jsonify({"messages": str(res)}), 500
    except Exception as e:
        return jsonify({"messages": str(e)}), 500

@insta_views.route('/<int:id>/download') 
def download(id):
    try:
        obj = obj_table.query.get(id)
        mobj = media.query.filter_by(resource_id=obj.id).first()
        if mobj and os.path.exists(mobj.media_path):
            print("Media already exists.")
            return send_file(mobj.media_path, as_attachment=True)
        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)
        status, res = ins.download()
        if status:
            med = media(media_path=res, resource_id=id)
            db.session.add(med)
            db.session.commit()
            return send_file(res, as_attachment=True)
        else:
            return jsonify({"messages": str(res)}), 500
    except Exception as e:
        return jsonify({"messages": e}), 500


@insta_views.route('/profile/<username>', methods=['GET'])
def get_profile_info(username):
    # Check rate limiting
    client_ip = request.remote_addr
    if is_rate_limited(client_ip):
        return jsonify({"messages": "Rate limit exceeded. Please try again later."}), 429

    try:
        # Try to get profile info without login first (for public profiles)
        ins = dInstagram(postUrl=f"https://www.instagram.com/{username}/")
        # For profile info, we need to get the user ID first
        try:
            user_id = ins.insta.user_id_from_username(username)
            ins.insta.login_by_sessionid(None)  # Try anonymous session
        except:
            # If anonymous doesn't work, we'll need credentials
            pass

        # Get profile info
        profile_info = ins.insta.user_info_by_username(username)

        # Extract relevant information
        profile_data = {
            'id': profile_info.pk,
            'username': profile_info.username,
            'full_name': profile_info.full_name,
            'biography': profile_info.biography,
            'external_url': profile_info.external_url,
            'follower_count': profile_info.follower_count,
            'following_count': profile_info.following_count,
            'is_private': profile_info.is_private,
            'is_verified': profile_info.is_verified,
            'profile_pic_url': profile_info.profile_pic_url,
            'media_count': profile_info.media_count
        }

        response = jsonify(profile_data)
        # Add rate limit headers
        headers = get_rate_limit_headers(client_ip)
        for key, value in headers.items():
            response.headers[key] = value
        return response, 200
    except instagrapi.exceptions.ChallengeRequired as e:
        return jsonify({"messages": "Instagram requires a security check. Please solve the challenge in your browser and try again later."}), 429
    except instagrapi.exceptions.LoginRequired as e:
        return jsonify({"messages": "Login required to view this profile. Please provide login credentials for private content."}), 401
    except instagrapi.exceptions.UserNotFound as e:
        return jsonify({"messages": "User not found. Please check the username."}), 404
    except instagrapi.exceptions.PrivateError as e:
        return jsonify({"messages": "This account is private. Please provide login credentials to view private content."}), 401
    except instagrapi.exceptions.ClientJSONDecodeError as e:
        return jsonify({"messages": "Instagram returned invalid response. The account may be private, restricted, or Instagram may be blocking requests."}), 500
    except instagrapi.exceptions.ClientError as e:
        if "We're sorry, but something went wrong" in str(e):
            return jsonify({"messages": "Instagram is experiencing issues or rate limiting requests. Please wait a few minutes and try again."}), 429
        else:
            return jsonify({"messages": str(e)}), 500
    except Exception as e:
        error_response = jsonify({"messages": str(e)}), 500
        # Add rate limit headers to error responses too
        headers = get_rate_limit_headers(client_ip)
        for key, value in headers.items():
            error_response[0].headers[key] = value
        return error_response


@insta_views.route('/profile/<username>/posts', methods=['GET'])
def get_user_posts(username):
    # Check rate limiting
    client_ip = request.remote_addr
    if is_rate_limited(client_ip):
        return jsonify({"messages": "Rate limit exceeded. Please try again later."}), 429

    try:
        ins = dInstagram(postUrl=f"https://www.instagram.com/{username}/")
        # Try to get user ID
        user_id = ins.insta.user_id_from_username(username)

        # Get recent posts (limit to 20 for performance)
        posts = ins.insta.user_medias(user_id, amount=20)

        # Serialize posts
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.pk,
                'code': post.code,
                'media_type': post.media_type,
                'thumbnail_url': post.thumbnail_url,
                'video_url': getattr(post, 'video_url', None),
                'caption_text': post.caption_text if post.caption else '',
                'like_count': post.like_count,
                'comment_count': post.comment_count,
                'taken_at': post.taken_at.isoformat() if post.taken_at else None
            })

        response = jsonify(posts_data), 200
        # Add rate limit headers
        headers = get_rate_limit_headers(client_ip)
        if isinstance(response, tuple):
            response_obj, status_code = response
            for key, value in headers.items():
                response_obj.headers[key] = value
            return response_obj, status_code
        else:
            for key, value in headers.items():
                response.headers[key] = value
            return response
    except instagrapi.exceptions.ChallengeRequired as e:
        return jsonify({"messages": "Instagram requires a security check. Please solve the challenge in your browser and try again later."}), 429
    except instagrapi.exceptions.LoginRequired as e:
        return jsonify({"messages": "Login required to view posts. Please provide login credentials for private content."}), 401
    except instagrapi.exceptions.UserNotFound as e:
        return jsonify({"messages": "User not found. Please check the username."}), 404
    except instagrapi.exceptions.PrivateError as e:
        return jsonify({"messages": "This account is private. Please provide login credentials to view private content."}), 401
    except instagrapi.exceptions.ClientJSONDecodeError as e:
        return jsonify({"messages": "Instagram returned invalid response. The account may be private, restricted, or Instagram may be blocking requests."}), 500
    except instagrapi.exceptions.ClientError as e:
        if "We're sorry, but something went wrong" in str(e):
            return jsonify({"messages": "Instagram is experiencing issues or rate limiting requests. Please wait a few minutes and try again."}), 429
        else:
            return jsonify({"messages": str(e)}), 500
    except Exception as e:
        error_response = jsonify({"messages": str(e)}), 500
        # Add rate limit headers to error responses too
        headers = get_rate_limit_headers(client_ip)
        if isinstance(error_response, tuple):
            error_obj, status_code = error_response
            for key, value in headers.items():
                error_obj.headers[key] = value
            return error_obj, status_code
        else:
            for key, value in headers.items():
                error_response.headers[key] = value
            return error_response


@insta_views.route('/profile/<username>/reels', methods=['GET'])
def get_user_reels(username):
    try:
        ins = dInstagram(postUrl=f"https://www.instagram.com/{username}/")
        user_id = ins.insta.user_id_from_username(username)

        # Get reels (clips) - filter media_type=2 and product_type=clips
        posts = ins.insta.user_medias(user_id, amount=50)  # Get more to filter

        reels_data = []
        for post in posts:
            if post.media_type == 2 and getattr(post, 'product_type', '') == 'clips':
                reels_data.append({
                    'id': post.pk,
                    'code': post.code,
                    'video_url': post.video_url,
                    'thumbnail_url': post.thumbnail_url,
                    'caption_text': post.caption_text if post.caption else '',
                    'like_count': post.like_count,
                    'comment_count': post.comment_count,
                    'taken_at': post.taken_at.isoformat() if post.taken_at else None
                })

        return jsonify(reels_data), 200
    except JSONDecodeError as e:
        return jsonify({"messages": "Instagram returned invalid response. The account may be private, restricted, or Instagram may be blocking requests."}), 500
    except Exception as e:
        return jsonify({"messages": str(e)}), 500


@insta_views.route('/profile/<username>/stories', methods=['GET'])
def get_user_stories(username):
    # Check rate limiting
    client_ip = request.remote_addr
    if is_rate_limited(client_ip):
        return jsonify({"messages": "Rate limit exceeded. Please try again later."}), 429

    try:
        ins = dInstagram(postUrl=f"https://www.instagram.com/{username}/")
        user_id = ins.insta.user_id_from_username(username)

        # Get stories
        stories = ins.insta.user_stories(user_id)

        # Serialize stories
        stories_data = []
        for story in stories:
            stories_data.append({
                'id': story.pk,
                'media_type': story.media_type,
                'thumbnail_url': story.thumbnail_url,
                'video_url': getattr(story, 'video_url', None),
                'taken_at': story.taken_at.isoformat() if story.taken_at else None,
                'expires_at': story.expires_at.isoformat() if story.expires_at else None
            })

        response = jsonify(stories_data), 200
        # Add rate limit headers
        headers = get_rate_limit_headers(client_ip)
        if isinstance(response, tuple):
            response_obj, status_code = response
            for key, value in headers.items():
                response_obj.headers[key] = value
            return response_obj, status_code
        else:
            for key, value in headers.items():
                response.headers[key] = value
            return response
    except instagrapi.exceptions.ChallengeRequired as e:
        return jsonify({"messages": "Instagram requires a security check. Please solve the challenge in your browser and try again later."}), 429
    except instagrapi.exceptions.LoginRequired as e:
        return jsonify({"messages": "Login required to view stories. Please provide login credentials for private content."}), 401
    except instagrapi.exceptions.UserNotFound as e:
        return jsonify({"messages": "User not found. Please check the username."}), 404
    except instagrapi.exceptions.PrivateError as e:
        return jsonify({"messages": "This account is private. Please provide login credentials to view private content."}), 401
    except instagrapi.exceptions.ClientJSONDecodeError as e:
        return jsonify({"messages": "Instagram returned invalid response. The account may be private, restricted, or Instagram may be blocking requests."}), 500
    except instagrapi.exceptions.ClientError as e:
        if "We're sorry, but something went wrong" in str(e):
            return jsonify({"messages": "Instagram is experiencing issues or rate limiting requests. Please wait a few minutes and try again."}), 429
        else:
            return jsonify({"messages": str(e)}), 500
    except Exception as e:
        error_response = jsonify({"messages": str(e)}), 500
        # Add rate limit headers to error responses too
        headers = get_rate_limit_headers(client_ip)
        if isinstance(error_response, tuple):
            error_obj, status_code = error_response
            for key, value in headers.items():
                error_obj.headers[key] = value
            return error_obj, status_code
        else:
            for key, value in headers.items():
                error_response.headers[key] = value
            return error_response


@insta_views.route('/profile/<username>/highlights', methods=['GET'])
def get_user_highlights(username):
    try:
        ins = dInstagram(postUrl=f"https://www.instagram.com/{username}/")
        user_id = ins.insta.user_id_from_username(username)

        # Get highlights
        highlights = ins.insta.highlight_highlight_reels(user_id)

        # Serialize highlights
        highlights_data = []
        for highlight in highlights:
            # Get highlight items ( Stories in the highlight )
            highlight_items = ins.insta.highlight(highlight.pk)

            items_data = []
            for item in highlight_items:
                items_data.append({
                    'id': item.pk,
                    'media_type': item.media_type,
                    'thumbnail_url': item.thumbnail_url,
                    'video_url': getattr(item, 'video_url', None),
                })

            highlights_data.append({
                'id': highlight.pk,
                'title': highlight.title,
                'cover_media_id': highlight.cover_media.pk if highlight.cover_media else None,
                'items': items_data
            })

        return jsonify(highlights_data), 200
    except JSONDecodeError as e:
        return jsonify({"messages": "Instagram returned invalid response. The account may be private, restricted, or Instagram may be blocking requests."}), 500
    except Exception as e:
        return jsonify({"messages": str(e)}), 500


@insta_views.route('/post/<int:postId>/comments', methods=['GET'])
def get_post_comments(postId):
    # Check rate limiting
    client_ip = request.remote_addr
    if is_rate_limited(client_ip):
        return jsonify({"messages": "Rate limit exceeded. Please try again later."}), 429

    try:
        # We need to find the object by its ID first
        obj = obj_table.query.get(postId)
        if not obj:
            return jsonify({"messages": "Post not found"}), 404

        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)

        # Get comments for the media
        comments = ins.insta.media_comments(postId)

        # Serialize comments
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': comment.pk,
                'text': comment.text,
                'user': {
                    'id': comment.user.pk,
                    'username': comment.user.username,
                    'full_name': comment.user.full_name,
                    'profile_pic_url': comment.user.profile_pic_url
                },
                'created_at': comment.created_at.isoformat(),
                'like_count': comment.like_count
            })

        response = jsonify(comments_data), 200
        # Add rate limit headers
        headers = get_rate_limit_headers(client_ip)
        if isinstance(response, tuple):
            response_obj, status_code = response
            for key, value in headers.items():
                response_obj.headers[key] = value
            return response_obj, status_code
        else:
            for key, value in headers.items():
                response.headers[key] = value
            return response
    except JSONDecodeError as e:
        return jsonify({"messages": "Instagram returned invalid response. The account may be private, restricted, or Instagram may be blocking requests."}), 500
    except Exception as e:
        error_response = jsonify({"messages": str(e)}), 500
        # Add rate limit headers to error responses too
        headers = get_rate_limit_headers(client_ip)
        if isinstance(error_response, tuple):
            error_obj, status_code = error_response
            for key, value in headers.items():
                error_obj.headers[key] = value
            return error_obj, status_code
        else:
            for key, value in headers.items():
                error_response.headers[key] = value
            return error_response


@insta_views.route('/post/<int:postId>/likes', methods=['GET'])
def get_post_likes(postId):
    # Check rate limiting
    client_ip = request.remote_addr
    if is_rate_limited(client_ip):
        return jsonify({"messages": "Rate limit exceeded. Please try again later."}), 429

    try:
        # We need to find the object by its ID first
        obj = obj_table.query.get(postId)
        if not obj:
            return jsonify({"messages": "Post not found"}), 404

        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)

        # Get users who liked the media
        likers = ins.insta.media_likers(postId)

        # Serialize likers
        likers_data = []
        for user in likers:
            likers_data.append({
                'id': user.pk,
                'username': user.username,
                'full_name': user.full_name,
                'is_private': user.is_private,
                'profile_pic_url': user.profile_pic_url
            })

        response = jsonify(likers_data), 200
        # Add rate limit headers
        headers = get_rate_limit_headers(client_ip)
        if isinstance(response, tuple):
            response_obj, status_code = response
            for key, value in headers.items():
                response_obj.headers[key] = value
            return response_obj, status_code
        else:
            for key, value in headers.items():
                response.headers[key] = value
            return response
    except JSONDecodeError as e:
        return jsonify({"messages": "Instagram returned invalid response. The account may be private, restricted, or Instagram may be blocking requests."}), 500
    except Exception as e:
        error_response = jsonify({"messages": str(e)}), 500
        # Add rate limit headers to error responses too
        headers = get_rate_limit_headers(client_ip)
        if isinstance(error_response, tuple):
            error_obj, status_code = error_response
            for key, value in headers.items():
                error_obj.headers[key] = value
            return error_obj, status_code
        else:
            for key, value in headers.items():
                error_response.headers[key] = value
            return error_response


@insta_views.route('/profile/<username>/followers', methods=['GET'])
def get_user_followers(username):
    try:
        ins = dInstagram(postUrl=f"https://www.instagram.com/{username}/")
        user_id = ins.insta.user_id_from_username(username)

        # Get followers (limit to 100 for performance)
        followers = ins.insta.user_followers(user_id, amount=100)

        # Serialize followers
        followers_data = []
        for user in followers:
            followers_data.append({
                'id': user.pk,
                'username': user.username,
                'full_name': user.full_name,
                'is_private': user.is_private,
                'profile_pic_url': user.profile_pic_url
            })

        return jsonify(followers_data), 200
    except JSONDecodeError as e:
        return jsonify({"messages": "Instagram returned invalid response. The account may be private, restricted, or Instagram may be blocking requests."}), 500
    except Exception as e:
        return jsonify({"messages": str(e)}), 500


@insta_views.route('/profile/<username>/following', methods=['GET'])
def get_user_following(username):
    try:
        ins = dInstagram(postUrl=f"https://www.instagram.com/{username}/")
        user_id = ins.insta.user_id_from_username(username)

        # Get following (limit to 100 for performance)
        following = ins.insta.user_following(user_id, amount=100)

        # Serialize following
        following_data = []
        for user in following:
            following_data.append({
                'id': user.pk,
                'username': user.username,
                'full_name': user.full_name,
                'is_private': user.is_private,
                'profile_pic_url': user.profile_pic_url
            })

        return jsonify(following_data), 200
    except JSONDecodeError as e:
        return jsonify({"messages": "Instagram returned invalid response. The account may be private, restricted, or Instagram may be blocking requests."}), 500
    except Exception as e:
        return jsonify({"messages": str(e)}), 500

