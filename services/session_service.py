import random
from dataclasses import astuple, dataclass, field
from datetime import timedelta
from datetime import datetime, timezone
from typing import List, Optional, NamedTuple, Dict

from services.scheduler import Scheduler
from models import Card, State, ReviewLog, Content, Rating
from db import CardCRUD, DeckCRUD, RevlogCRUD, MetadataCRUD, ContentCRUD
from utils import DEFAULT_DECK_ID, DEFAULT_DECK_NAME


# To-do: Cached queue? with cards due between session_cutoff and next_day?


@dataclass
class DeckCounts:
    new: int = 0
    learn: int = 0
    review: int = 0


@dataclass
class CurrentDeckData:
    deck_id: int = DEFAULT_DECK_ID
    deck_name: str = DEFAULT_DECK_NAME
    count: DeckCounts = field(default_factory=DeckCounts)


@dataclass
class StudySession:
    start_time: datetime
    cutoff_time: datetime
    limit_for_new_cards: int

    new_cards: List[Card] = field(default_factory=list)
    learn_cards: List[Card] = field(default_factory=list)
    review_cards: List[Card] = field(default_factory=list)

    cards_done_until_cutoff: List[Card] = field(default_factory=list)

    indexed_contents: Dict[int, Content] = field(default_factory=dict)

    review_logs: List[ReviewLog] = field(default_factory=list)

    def build_content_index(self, card_contents):
        self.indexed_contents = {c.id: c for c in card_contents} if card_contents is not None else {}


@dataclass
class CurrentCardData:
    card: Card
    content: Content


class AppContext(NamedTuple):
    scheduler: Scheduler = Scheduler()
    card_crud: CardCRUD = CardCRUD()
    deck_crud: DeckCRUD = DeckCRUD()
    content_crud: ContentCRUD = ContentCRUD()
    revlog_crud: RevlogCRUD = RevlogCRUD()
    metadata_crud: MetadataCRUD = MetadataCRUD()


class SessionService:
    DAILY_LIMIT_FOR_NEW_CARDS = 200
    SHOULD_LEARN_AHEAD = True
    LEARN_AHEAD_MINUTES = 60

    NEW_KEY = "new"
    LEARN_KEY = "learn"
    REVIEW_KEY = "review"

    LIST_PRIORITY_WEIGHTS = {
        NEW_KEY: 1,
        LEARN_KEY: 2,
        REVIEW_KEY: 1,
    }

    def __init__(self, deck_id: Optional[int] = None):
        self.context = AppContext()

        self.current_deck_data: CurrentDeckData = CurrentDeckData()
        self.current_card_data: Optional[CurrentCardData] = None
        self.session: Optional[StudySession] = None

        self.set_current_deck_id_and_name(deck_id=deck_id)
        self.start_new_session()

        self.list_priority_weights = SessionService.LIST_PRIORITY_WEIGHTS

        self.populate_session_lists()
        self.populate_session_indexed_contents()
        self.update_deck_counts()

    def start_new_session(self):
        start_time: datetime = datetime.now(timezone.utc)
        cutoff_time: datetime = start_time
        if SessionService.SHOULD_LEARN_AHEAD:
            cutoff_time += timedelta(minutes=SessionService.LEARN_AHEAD_MINUTES)
        limit_for_new_cards = self.get_session_limit_for_new_cards()

        self.session = StudySession(
            start_time=start_time,
            cutoff_time=cutoff_time,
            limit_for_new_cards=limit_for_new_cards
        )

    def set_current_deck_id_and_name(self, deck_id: Optional[int]):
        if deck_id is None:
            return
        deck_name = self.context.deck_crud.get_deck_by_id(deck_id)
        self.current_deck_data.deck_id = deck_id
        self.current_deck_data.deck_name = deck_name
        # self.update_deck_counts()

    @property
    def card_state_to_session_list(self):
        return {
            State.New | State.New.value: self.session.new_cards,
            State.Learning | State.Learning.value: self.session.learn_cards,
            State.Relearning | State.Learning.value: self.session.learn_cards,
            State.Review | State.Review.value: self.session.review_cards,
        }

    def get_session_limit_for_new_cards(self):
        metadata = self.context.metadata_crud.get_metadata()
        if metadata:
            (_, last_session_cutoff, new_cards_reviewed) = tuple(metadata[0])
            last_session_cutoff = datetime.fromisoformat(last_session_cutoff)

            if last_session_cutoff.day == self.session.cutoff_time.day:
                return max((SessionService.DAILY_LIMIT_FOR_NEW_CARDS - new_cards_reviewed), 0)

        return SessionService.DAILY_LIMIT_FOR_NEW_CARDS

    def populate_session_lists(self):  # To-do: pass deck_id!!!!
        # print("session_service.py -> populate_session_lists")
        cards = self.get_session_new_cards_within_limit()
        self.session.new_cards = [Card(*card) for card in cards]

        cards = self.get_session_learn_cards()  # pass last session cutoff and now for due between ?, ?
        self.session.learn_cards = [Card(*card) for card in cards]

        cards = self.get_session_review_cards()  # pass last session cutoff and now for due between ?, ?
        self.session.review_cards = [Card(*card) for card in cards]

    def gather_session_content_ids(self):
        if not self.has_cards_to_study():
            return None

        content_ids = []
        if self.session.new_cards:
            content_ids.extend([card.content_id for card in self.session.new_cards])
        if self.session.learn_cards:
            content_ids.extend([card.content_id for card in self.session.learn_cards])
        if self.session.review_cards:
            content_ids.extend([card.content_id for card in self.session.review_cards])

        return content_ids

    def populate_session_indexed_contents(self):
        content_ids = self.gather_session_content_ids()
        contents = self.context.content_crud.get_many_contents_by_ids(content_ids)
        contents = [Content(*content) for content in contents]
        self.session.build_content_index(card_contents=contents)

    def update_deck_counts(self):
        self.current_deck_data.count.new = len(self.session.new_cards) if self.session.new_cards is not None else 0
        self.current_deck_data.count.learn = len(self.session.learn_cards) if self.session.learn_cards is not None else 0
        self.current_deck_data.count.review = len(self.session.review_cards) if self.session.review_cards is not None else 0

    def get_session_cutoff(self):
        if SessionService.SHOULD_LEARN_AHEAD:
            return self.session.start_time + timedelta(minutes=SessionService.LEARN_AHEAD_MINUTES)
        return self.session.start_time

    def get_session_new_cards_within_limit(self):  # To-do: pass new session limit!!
        # print("session_service.py -> get_session_new_cards_within_limit")
        # print(f"session_limit_for_new_cards: {self.session_limit_for_new_cards}")
        return self.context.card_crud.get_limited_new_cards(
            deck_id=self.current_deck_data.deck_id,
            new_state_int=State.New,
            limit=self.session.limit_for_new_cards
        )

    def get_session_learn_cards(self):  # To-do: add due!!
        return self.context.card_crud.get_due_learning_cards(
            deck_id=self.current_deck_data.deck_id,
            learning_state_int=State.Learning,
            relearning_state_int=State.Relearning,
            session_cutoff_epoch_millis=Scheduler.date_to_epoch_millis(self.session.cutoff_time)
        )

    def get_session_review_cards(self):  # To-do: add due!!  change deck_id !!!
        return self.context.card_crud.get_due_review_cards(
            deck_id=self.current_deck_data.deck_id,
            review_state_int=State.Review,
            session_cutoff_epoch_millis=Scheduler.date_to_epoch_millis(self.session.cutoff_time)
        )

    def has_day_changed(self):
        if datetime.now(timezone.utc).day > self.session.cutoff_time.day:
            return True
        return False

    def update_session_span(self):
        self.session.start_time = datetime.now(timezone.utc)
        self.session.cutoff_time = self.get_session_cutoff()

    def on_day_change(self):
        self.update_cards_in_db()
        self.clear_session_lists()

        self.update_session_span()
        self.populate_session_lists()
        self.update_deck_counts()

    def match_and_append_to_list(self, updated_card):
        target_list = self.card_state_to_session_list.get(updated_card.state)
        if target_list is not None:
            target_list.append(updated_card)
            # target_list.sort(key=lambda card: card.due)
        else:
            print("match_and_append_to_list failed")

    def on_answer(self, card, rating, review_datetime, review_duration):
        updated_card, review_log = self.context.scheduler.review_card(card, rating, review_datetime, review_duration)

        self.session.review_logs.append(review_log)

        if updated_card.due > Scheduler.date_to_epoch_millis(self.session.cutoff_time):
            self.session.cards_done_until_cutoff.append(updated_card)

        else:
            self.match_and_append_to_list(updated_card)
            self.update_deck_counts()

    def _precompute_selection_data(self):
        """Pre-compute all selection data for O(1) lookup"""
        w = self.list_priority_weights
        k_new = SessionService.NEW_KEY
        k_learn = SessionService.LEARN_KEY
        k_review = SessionService.REVIEW_KEY
        w_new = w[k_new]
        w_learn = w[k_learn]
        w_review = w[k_review]

        # Pre-compute cumulative weights for all 7 possible combinations
        self._selection_data = {
            # (has_new, has_learn, has_review): (cumulative_thresholds, names)
            (True, True, True): ([w_new, w_new + w_learn], [k_new, k_learn, k_review]),
            (True, True, False): ([w_new], [k_new, k_learn]),
            (True, False, True): ([w_new], [k_new, k_review]),
            (False, True, True): ([w_learn], [k_learn, k_review]),
            (True, False, False): ([], [k_new]),
            (False, True, False): ([], [k_learn]),
            (False, False, True): ([], [k_review]),
        }

        # Pre-compute total weights for normalization
        self._total_weights = {
            (True, True, True): w_new + w_learn + w_review,
            (True, True, False): w_new + w_learn,
            (True, False, True): w_new + w_review,
            (False, True, True): w_learn + w_review,
            (True, False, False): w_new,
            (False, True, False): w_learn,
            (False, False, True): w_review,
        }
        self._list_refs = {
            k_new: self.session.new_cards,  # Reference to existing list
            k_learn: self.session.learn_cards,  # Reference to existing list
            k_review: self.session.review_cards  # Reference to existing list
        }

    def has_cards_to_study(self):
        has_new = len(self.session.new_cards) > 0
        has_learn = len(self.session.learn_cards) > 0
        has_review = len(self.session.review_cards) > 0
        return has_new or has_learn or has_review

    def choose_weighted_list_name(self) -> Optional[str]:
        """
        Optimized weighted selection using pre-computed cumulative weights.
        Time: O(1), Space: O(1)
        """
        if not self.has_cards_to_study():
            return None

        has_new = len(self.session.new_cards) > 0
        has_learn = len(self.session.learn_cards) > 0
        has_review = len(self.session.review_cards) > 0

        self._precompute_selection_data()
        # O(1) lookup of pre-computed weights
        combination_key = (has_new, has_learn, has_review)

        cumulative_weights, names = self._selection_data[combination_key]

        # Single list case - no random selection needed
        if len(names) == 1:
            return names[0]

        # Fast weighted selection using cumulative weights
        if len(names) == 2:
            # Two lists: simple threshold check
            total_weight = cumulative_weights[0] + (
                self.list_priority_weights[names[1]] if len(cumulative_weights) == 1
                else sum(self.list_priority_weights[name] for name in names) - cumulative_weights[0]
            )
            if random.random() * total_weight < cumulative_weights[0]:
                return names[0]
            return names[1]
        else:
            # Three lists: two threshold checks
            total_weight = sum(self.list_priority_weights[name] for name in names)
            rand_val = random.random() * total_weight

            if rand_val < cumulative_weights[0]:
                return names[0]
            elif rand_val < cumulative_weights[1]:
                return names[1]
            else:
                return names[2]

    def set_next_card(self) -> None:
        selected_list_name = self.choose_weighted_list_name()
        # Fast empty check before expensive selection
        if not selected_list_name:
            return

        # Direct list access without string comparison overhead
        selected_list = self._list_refs[selected_list_name]
        cc = selected_list.pop(0)
        assert cc is not None
        selected_list.sort(key=lambda card: card.due)  # sorted after popping to avoid seeing the same card next

        content = self.session.indexed_contents.get(cc.content_id)
        self.current_card_data = CurrentCardData(cc, content)

    def gather_all_updated_cards(self):
        updated_cards = (self.session.cards_done_until_cutoff
                         + self.session.learn_cards
                         + self.session.review_cards
                         + self.session.new_cards)
        return updated_cards

    def update_cards_in_db(self):
        updated_cards = self.gather_all_updated_cards()

        updated_cards_dict: List[dict] = [uc.to_dict() for uc in updated_cards]

        self.context.card_crud.update_many_cards(updated_cards_dict=updated_cards_dict)

    def clear_session_lists(self):
        self.session.cards_done_until_cutoff = []
        self.session.review_cards = []
        self.session.learn_cards = []
        self.session.new_cards = []

    def on_session_end(self):
        if self.session.review_logs and len(self.session.review_logs) > 0:
            self.context.revlog_crud.insert_many_reviews([astuple(rv) for rv in self.session.review_logs])
            self.update_cards_in_db()
            new_cards_reviewed = max(self.session.limit_for_new_cards - len(self.session.new_cards), 0)

            self.clear_session_lists()
            self.update_deck_counts()
            self.context.metadata_crud.insert_or_replace_metadata(
                last_session_cutoff=self.session.cutoff_time,
                new_cards_reviewed=new_cards_reviewed
            )

        else:
            print("No cards studied in this session!")
        # -- TO-DO create config table with CAPS_CONSTANTS


def run():
    session_service = SessionService()
    content_crud = ContentCRUD()

    # do stuff

    session_service.on_session_end()


def simulate_session():
    ss = SessionService()

    while ss.has_cards_to_study():
        ss.set_next_card()

        # ---------- Replace with actual fetching, showing and answering
        rating = random.choice([Rating.Hard, Rating.Easy, Rating.Good, Rating.Again])
        review_datetime = datetime.now(timezone.utc)
        review_duration = 30
        print("Rating: ", rating, "\t\tState: ", ss.current_card_data.card.state, ss.current_card_data.content.de, ss.current_card_data.content.en)
        # ---------- END Replace with actual fetching, showing and answering

        ss.on_answer(ss.current_card_data.card, rating, review_datetime, review_duration)
    ss.on_session_end()


def test_singleton():
    a = ContentCRUD()
    b = ContentCRUD()
    assert a is b, "Singleton test failed"


def test():
    query = "SELECT * FROM cards WHERE state <> ?"
    params = (0,)

    card_crud = CardCRUD()
    content_crud = ContentCRUD()

    not_new_cards = card_crud.execute_select_many(query, params)

    for c in not_new_cards:
        c = Card(*c)
        print(c)
        c_con = content_crud.get_content_by_id(c.content_id)
        c_con = Content(*c_con)
        print(c_con.de, c_con.en)

    print(len(not_new_cards))


if __name__ == "__main__":
    test_singleton()
