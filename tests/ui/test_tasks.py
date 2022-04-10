from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from tests.utils import unique_str, unique_int

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_task_html_id(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([title])

    task_id = unique_int()
    db.tasks.create_by_ids([task_id])

    group_id = next(group.id for group in db.groups.get_by_prefix(prefix))
    response = client.get(f'/group/{group_id}')
    html_group = response.get_data(as_text=True)

    tag_contents = [tag for tag in get_tags(html_group, 'a', 'text-decoration-none')
                    if f'№{task_id + 1}' in tag.get_text()]

    assert len(tag_contents) == 1


def test_task_html_link(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    group_title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([group_title])

    task_id = unique_int()
    db.tasks.create_by_ids([task_id])

    group_id = next(group.id for group in db.groups.get_by_prefix(prefix))
    response = client.get(f'/group/{group_id}')
    html_group = response.get_data(as_text=True)

    tag_contents = next(tag.get('href') for tag in get_tags(html_group, 'a', 'text-decoration-none')
                        if f'№{task_id + 1}' in tag.get_text())

    assert tag_contents == f'http://sovietov.com/kispython/{task_id}/{group_title}.html'


def get_tags(html: str, name: str, class_: str) -> ResultSet[Tag]:
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all(name, class_=class_)
