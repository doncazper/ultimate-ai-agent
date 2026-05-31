from enum import Enum


class ProviderDomain(str, Enum):
    weather = "weather"
    news = "news"
    search = "search"
    reddit = "reddit"
    email = "email"
    messages = "messages"
    calendar = "calendar"
    github = "github"
    maps = "maps"
    finance = "finance"
    generic = "generic"


class ProviderAuthRequirement(str, Enum):
    none = "none"
    optional_key = "optional_key"
    required_key = "required_key"
    oauth_required = "oauth_required"
    service_account_required = "service_account_required"


class ProviderCostClass(str, Enum):
    free_no_key = "free_no_key"
    free_with_key = "free_with_key"
    paid = "paid"
    enterprise = "enterprise"
    self_hosted = "self_hosted"


class ProviderStatus(str, Enum):
    enabled = "enabled"
    disabled = "disabled"
    unavailable = "unavailable"
    deprecated = "deprecated"
    blocked = "blocked"


class ProviderCapability(str, Enum):
    current_weather = "current_weather"
    weather_forecast = "weather_forecast"
    weather_alerts = "weather_alerts"
    news_search = "news_search"
    top_headlines = "top_headlines"
    article_lookup = "article_lookup"
    web_search = "web_search"
    reddit_search = "reddit_search"
    email_search = "email_search"
    calendar_read = "calendar_read"
    generic_query = "generic_query"
