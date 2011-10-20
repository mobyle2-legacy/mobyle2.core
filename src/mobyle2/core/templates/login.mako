<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
  <head>
    <title>The Pyramid Web Application Development Framework</title>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <link rel="shortcut icon" href="${request.static_url('birdie:static/favicon.ico')}" />
    <link rel="stylesheet" href="${request.static_url('birdie:static/pylons.css')}" type="text/css" media="screen" charset="utf-8" />
    <link rel="stylesheet" href="http://static.pylonsproject.org/fonts/nobile/stylesheet.css" media="screen">
      <link rel="stylesheet" href="http://static.pylonsproject.org/fonts/neuton/stylesheet.css" media="screen">
      </head>
      <body>
        <div id="wrap">
          <div id="top-small">
            <div class="top-small">
              <div><img src="${request.static_url('birdie:static/pyramid-small.png')}" width="220" height="50" alt="pyramid"/>
              <div id="top-legend">Pyramid Tutorial demo application - Stage 3</div>
            </div>
          </div>
        </div>
        <div id="middle">
          <div class="middle">
            <h1 class="app-welcome">
              <a href="${app_url}">Birdie</a>
            </h1>
            <p>What are you up to?</p>
          </div>
        </div>
        <div id="bottom">
          <div class="bottom">
            <h1>Birdie Login</h1>
            <div id="message">
              <p>${message}</p>
            </div>
            <form action="${app_url}" method="POST">
              Username: <input type="text" name="login" value="${login}" />
              <br />
              Password: <input type="password" name="password" value="" />
              <br />
              <input type="submit" value="login" />
            </form>
            <div id="join">
              <p>Not a member? <a href="${app_url}/join">Sign up now.</a></p>
            </div>
          </div>
        </div>
      </div>
      <div id="footer">
        <div class="footer">&copy; Copyright 2011, Carlos de la Guardia.</div>
      </div>
    </body>
  </html> 
