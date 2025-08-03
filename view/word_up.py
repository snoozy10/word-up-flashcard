from threading import Thread

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ttkbootstrap.dialogs import Messagebox

from db import DatabaseInitializer, DatabaseBaseClass
from services import SessionService
from view import UIElements


class WordUp:
    app_theme = "superhero"  # cosmo, superhero, sandstone
    app_name = "WordUP!"
    app_geometry = "560x800"
    win_width = 560
    font_primary = "Yu Gothic UI"
    font_secondary = "Segoe UI"
    btn_primary = "default-outline"
    btn_warning = "warning-outline"
    padding_mainframe = 30
    padding_lframe = 20
    padding_floodgauge = 10
    ipad_btn = 6

    def __init__(self, window):
        self.window = window

        self.mainframe = ttk.Frame(self.window)
        self.mainframe.configure(padding=WordUp.padding_mainframe)
        self.mainframe.pack(fill=BOTH, expand=YES)
        self.config_styles()

        self.ui_front: bool = True
        self.db_overwrite_prompt: bool = True
        self.ui_elements = None
        self.current_deck = None
        self.current_card = None

        self.progress = ttk.Progressbar(self.mainframe, mode="indeterminate")
        self.progress.pack(
            expand=YES,
            fill=X,
            anchor="center",
            pady=WordUp.padding_mainframe
        )
        self.progress.start()

        self.session_service = None
        self.db_initializer = DatabaseInitializer()
        self.window.after(0, self.start_initialization_thread)

    def start_initialization_thread(self):
        thread = Thread(target=self.init_db_and_session_service, daemon=True)
        thread.start()

    def init_db_and_session_service(self):
        # UI must prompt in main thread
        db_exists = self.db_initializer.database_exists()
        if db_exists and self.db_overwrite_prompt:
            self.window.after(0, self.prompt_db_overwrite_and_continue)
        else:
            self.continue_initialization()

    def prompt_db_overwrite_and_continue(self):
        answer = Messagebox.show_question(
            parent=self.window,
            title="Overwrite Existing Database?",
            buttons=['Yes:danger-outline', 'No:default'],
            message=(
                f"A database already exists at {self.db_initializer.db_path}.\n"
                "Do you want to overwrite it?\n\n"
                "WARNING: This action cannot be undone!"
            ),
            alert=False
        )
        if answer == "Yes":
            answer = Messagebox.show_question(
                parent=self.window,
                title="Overwrite Existing Database?",
                buttons=['Yes:danger-outline', 'No:default'],
                message=(
                    f"Are you sure?\n\n"
                    "WARNING: This action cannot be undone!"
                ),
                alert=True
            )
            if answer == "Yes":
                # To-do: add backup
                self.db_initializer.delete_existing_database()

        # DB init in worker thread
        Thread(target=self.continue_initialization, daemon=True).start()

    def continue_initialization(self):
        self.db_initializer.initialize_database()
        _ = DatabaseBaseClass()
        self.session_service = SessionService()

        # UI update on main thread
        self.window.after(0, self.on_init_db_and_session_service)

    def on_init_db_and_session_service(self):
        self.progress.stop()
        self.progress.destroy()
        self.load_ui_elements()
        self.window.protocol("WM_DELETE_WINDOW", self.on_exit)

    def load_ui_elements(self):
        if self.session_service.has_cards_to_study():
            self.ui_elements = UIElements()

            self.session_service.set_next_card()

            self.load_topframe()  # needs deck_name/deck_id
            self.load_midframe()  # needs card content!
            self.load_bottomframe()  # needs intervals

        else:
            self.mainframe.destroy()
            self.load_end_message()

    def load_end_message(self):
        lbl_empty_msg = ttk.Label(
            master=self.window,
            text="Woohoo! No cards to study for now!",
            style="fontLarge.TLabel",
            justify="center"
        )
        lbl_empty_msg.pack(expand=YES, anchor="center")
        self.session_service.on_session_end()
        # self.window.protocol("WM_DELETE_WINDOW", None)

    @staticmethod
    def config_styles():
        s = ttk.Style()
        color = s.colors.get('warning')

        ttk.Style().configure('TButton', font=(WordUp.font_primary, 12, 'bold'))
        ttk.Style().configure('fontLarge.TLabel', font=(WordUp.font_primary, 12, 'bold'))
        ttk.Style().configure('fontXLarge.TLabel', font=(WordUp.font_primary, 18, 'bold'), foreground=color)
        ttk.Style().configure('fontMedium.TLabel', font=(WordUp.font_secondary, 9))
        ttk.Style().configure('fontSmall.TLabel', font=(WordUp.font_secondary, 9))
        ttk.Style().configure('TLabelframe', font=(WordUp.font_primary, 12))

    def load_topframe(self):
        uie = self.ui_elements
        uie.frame_top = ttk.Frame(self.mainframe)
        uie.frame_top.pack(fill=X, anchor=N)

        # To-do btn_menu action
        uie.btn_menu = ttk.Button(uie.frame_top, text="\u2630", bootstyle=WordUp.btn_primary)
        uie.btn_menu.pack(side=LEFT, ipadx=WordUp.ipad_btn, ipady=WordUp.ipad_btn)

        uie.frame_deck_info = ttk.Frame(uie.frame_top)  # frame to hold name and info of deck
        uie.frame_deck_info.pack(side=LEFT, padx=WordUp.padding_mainframe)

        # To-do: pass deck_name and deck_counts
        # controller: lbl_deck_name, lbl_deck_counts
        uie.lbl_deck_name = ttk.Label(
            uie.frame_deck_info,
            text=self.session_service.current_deck_data.deck_name,
            style="fontLarge.TLabel"
        )
        uie.lbl_deck_name.pack(side=TOP, anchor=W, padx=0)

        count_txt = self._get_count_txt()

        uie.lbl_deck_counts = ttk.Label(
            uie.frame_deck_info, text=count_txt, style="fontMedium.TLabel"
        )
        uie.lbl_deck_counts.pack(side=BOTTOM, anchor=W, padx=0)

        # uie.btn_exit = ttk.Button(uie.frame_top, text="\u23FB", bootstyle=WordUp.btn_warning)
        # uie.btn_exit.pack(side=RIGHT, ipadx=WordUp.ipad_btn, ipady=WordUp.ipad_btn)

    def _get_count_txt(self):
        new = self.session_service.current_deck_data.count.new
        learn = self.session_service.current_deck_data.count.learn
        review = self.session_service.current_deck_data.count.review
        done = self.session_service.current_deck_data.count.done_for_today

        return f"New: {new}  |  Learn: {learn}  |  Due:  {review}  |  Done: {done}"

    def load_midframe(self):
        uie = self.ui_elements
        # To-do: pass language (de or en) and card front and back
        # controller: lframe_mid text, lbl_card text
        uie.lframe_mid = ttk.Labelframe(
            master=self.mainframe,
            text="de"
        )
        uie.lframe_mid.configure(borderwidth=2, relief="solid")
        uie.lframe_mid.pack(
            fill=BOTH,
            expand=YES,
            pady=WordUp.padding_lframe
        )
        uie.lbl_card = ttk.Label(
            uie.lframe_mid,
            text=self.session_service.current_card_data.content.de,
            wraplength=WordUp.win_width * 0.75,
            justify="center",
            style="fontXLarge.TLabel"
        )
        uie.lbl_card.pack(expand=YES, anchor="center")

    def load_bottomframe(self):
        uie = self.ui_elements
        uie.frame_bottom = ttk.Frame(self.mainframe)
        uie.frame_bottom.pack(fill=X)

        if self.ui_front:
            self._load_bottom_widgets_front()

        else:
            self._load_bottom_widgets_back()

    def _onclick_btn_show_answer(self):
        self.ui_front = False
        self._update_lframe_mid()
        self._reload_frame_bottom()

    def _update_frame_top(self):
        uie = self.ui_elements
        uie.lbl_deck_counts.configure(text=self._get_count_txt())

    def _update_lframe_mid(self):
        uie = self.ui_elements
        if self.ui_front:
            uie.lframe_mid.configure(text="de")
            uie.lbl_card.configure(text=self.session_service.current_card_data.content.de)
        else:
            uie.lframe_mid.configure(text="en")
            uie.lbl_card.configure(text=self.session_service.current_card_data.content.en)

    def _reload_frame_bottom(self):
        uie = self.ui_elements
        for widget in uie.frame_bottom.winfo_children():
            widget.pack_forget()
        if self.ui_front:
            self._load_bottom_widgets_front()
        else:
            self._load_bottom_widgets_back()

    def _load_lbl_btn_composite(self, txt_lbl, txt_btn, bootstyle):
        uie = self.ui_elements
        frame_btn_composite = ttk.Frame(master=uie.frame_bottom)
        frame_btn_composite.pack(side=LEFT, expand=YES, ipadx=0)

        lbl_interval = ttk.Label(frame_btn_composite, text=txt_lbl, style='fontMedium.TLabel')
        lbl_interval.pack(pady=(8, 10))  # To-do: improve

        btn_rating = ttk.Button(frame_btn_composite, text=txt_btn, bootstyle=bootstyle)
        btn_rating.config(command=lambda b=btn_rating: self._onclick_btn_rating(b))
        btn_rating.pack(fill=X, ipadx=WordUp.ipad_btn*3, ipady=WordUp.ipad_btn)

        return frame_btn_composite, lbl_interval, btn_rating

    def _load_bottom_widgets_back(self):
        uie = self.ui_elements
        ivl_again, ivl_hard, ivl_good, ivl_easy = self.session_service.get_next_intervals()

        if not (uie.frame_again and uie.frame_hard and uie.frame_good and uie.frame_easy):
            uie.frame_again, uie.lbl_again, uie.btn_again \
                = self._load_lbl_btn_composite(ivl_again, "Again", 'warning-outline')
            uie.frame_hard, uie.lbl_hard, uie.btn_hard \
                = self._load_lbl_btn_composite(ivl_hard, "Hard", 'default-outline')
            uie.frame_good, uie.lbl_good, uie.btn_good \
                = self._load_lbl_btn_composite(ivl_good, "Good", 'default-outline')
            uie.frame_easy, uie.lbl_easy, uie.btn_easy \
                = self._load_lbl_btn_composite(ivl_easy, "Easy", 'default-outline')

        else:
            uie.lbl_again.configure(text=ivl_again)
            uie.lbl_hard.configure(text=ivl_hard)
            uie.lbl_good.configure(text=ivl_good)
            uie.lbl_easy.configure(text=ivl_easy)
            uie.frame_again.pack(side=LEFT, expand=YES, ipadx=0)
            uie.frame_hard.pack(side=LEFT, expand=YES, ipadx=0)
            uie.frame_good.pack(side=LEFT, expand=YES, ipadx=0)
            uie.frame_easy.pack(side=LEFT, expand=YES, ipadx=0)

    def _onclick_btn_rating(self, btn_rating):
        self.session_service.on_answer(rating_txt=btn_rating['text'], review_duration=None)
        self.ui_front = not self.ui_front

        if self.session_service.has_cards_to_study():
            self._update_frame_top()
            self._update_lframe_mid()
            self._reload_frame_bottom()
        else:
            self.mainframe.destroy()
            self.load_end_message()

    def _load_bottom_widgets_front(self):
        uie = self.ui_elements
        # To-do: Thread for timer and text!!!
        # controller: floodgauge_timer value and text
        if not uie.floodgauge_timer:
            uie.floodgauge_timer = ttk.Floodgauge(master=uie.frame_bottom, orient=HORIZONTAL, value=53, text="0m : 45s",
                                               bootstyle=SECONDARY, thickness=15, font=(WordUp.font_secondary, 8))
        uie.floodgauge_timer.pack(fill=X, ipady=WordUp.ipad_btn, pady=WordUp.padding_floodgauge)

        if not uie.btn_answer:
            uie.btn_answer = ttk.Button(master=uie.frame_bottom, text="Show Answer", style=WordUp.btn_primary,
                                    command=self._onclick_btn_show_answer)
        uie.btn_answer.pack(fill=X, ipadx=WordUp.ipad_btn, ipady=WordUp.ipad_btn)

    def on_exit(self):
        if self.session_service.has_cards_to_study():
            answer = Messagebox.show_question(
                parent=self.window,
                title="End Session?",
                buttons=['Yes:danger-outline', 'No:default'],
                message=(
                    "Do you really want to end this session?"
                ),
                alert=True
            )
            if answer == "Yes":
                self.window.destroy()
                self.session_service.on_session_end()
        else:
            self.window.destroy()


# DEPRECATED
def legacy_code(frame_progressbar):
    frame_info = ttk.Frame(
        master=frame_progressbar
    )
    frame_info.pack(
        fill=X,
        pady=5
    )
    lbl_infotext = ttk.Label(frame_info, text="0m : 45s", style="fontSmall.TLabel")
    lbl_infotext.pack(fill=X, expand=YES)

    progressbar = ttk.Progressbar(
        master=frame_progressbar,
        orient=HORIZONTAL,
        value=75,
        bootstyle=STRIPED
    )
    progressbar.pack(fill=X)
