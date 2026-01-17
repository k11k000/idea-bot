import disnake
from disnake.ext import commands
from disnake import SelectOption
from dotenv import load_dotenv
import methods
import sqlite3
import math
import os

load_dotenv("config.env")
IDEA_CHANNEL_ID = os.getenv("IDEA_CHANNEL_ID")
if not IDEA_CHANNEL_ID:
    print("[!] Не найден IDEA_CHANNEL_ID в config.env")
    raise 
IDEA_CHANNEL_ID = int(IDEA_CHANNEL_ID)

def user_check(func):
    async def wrapper(self, inter: disnake.MessageInteraction, *args, **kwargs):
        if inter.author.id != self.self_view.user.id:
            return await inter.response.send_message("Интеракция вызвана не тобой!", ephemeral=True)
        return await func(self, inter, *args, **kwargs)
    return wrapper

def get_ideas(sort_by="likes"):
    with sqlite3.connect("ideas.db") as db:
        cursor = db.cursor()
        cursor.execute(f"SELECT name, likes, dislikes, answer, id FROM ideas ORDER BY (answer IS NOT NULL AND answer != '') ASC, {sort_by} DESC")
        ideas = cursor.fetchall()
        return ideas

def get_idea(idea_id):
    with sqlite3.connect("ideas.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT name, description, likes, dislikes, answer, id, author_id FROM ideas WHERE id = ?", (idea_id,))
        idea = cursor.fetchone()
        return idea

class IdeasView(disnake.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user
        self.page = 1
        self.sort_by = "likes"
        if user:
            self.update_page()

    def update_page(self):
        ideas = get_ideas(self.sort_by)
        if ideas:
            pages = math.ceil(len(ideas) / 5)
            count_start = (self.page - 1) * 5
            count_end = min(count_start + 5, len(ideas))

            text = ""
            options = []

            for count in range(count_start, count_end):
                idea = ideas[count]
                name, likes, dislikes, answer, idea_id = idea

                text += f"""
                **Идея #{count + 1}**
                ・**Название:** {name}
                ・**Лайки:** {likes}
                ・**Дизлайки:** {dislikes}
                ・**Ответ:** {answer or "—"}
                """

                if len(options) < 25:
                    options.append(SelectOption(label=f"Идея #{count + 1}", description=name[:100], value=str(idea_id)))

            self.embed = methods.embed(f"Список идей {self.page}/{pages}", text)
            
            self.clear_items()

            dropdown = self.IdeasDropdown(self, options)
            sort = self.SortDropdown(self)
            back = self.BackPageButton(self)
            forward = self.NextPageButton(self)
            search = self.SearchButton(self)

            if self.page == 1:
                back.disabled = True
            if pages == self.page:
                forward.disabled = True

            self.add_item(back)
            self.add_item(forward)
            self.add_item(search)
            self.add_item(dropdown)
            self.add_item(sort)
        else:
            self.embed = methods.embed("Список идей", "Пусто.")

    class NextPageButton(disnake.ui.Button):
        def __init__(self, self_view):
            super().__init__(label=">", style=disnake.ButtonStyle.gray, custom_id="next_page")
            self.self_view = self_view  

        @user_check
        async def callback(self, inter: disnake.MessageInteraction):
            self.self_view.page += 1  
            self.self_view.update_page() 
            await inter.response.edit_message(embed=self.self_view.embed, view=self.self_view)  

    class BackPageButton(disnake.ui.Button):
        def __init__(self, self_view):
            super().__init__(label="<", style=disnake.ButtonStyle.gray, custom_id="prev_page")
            self.self_view = self_view  

        @user_check
        async def callback(self, inter: disnake.MessageInteraction):
            self.self_view.page -= 1  
            self.self_view.update_page() 
            await inter.response.edit_message(embed=self.self_view.embed, view=self.self_view)  

    class SearchButton(disnake.ui.Button):
        def __init__(self, self_view):
            super().__init__(emoji="🔎", style=disnake.ButtonStyle.blurple, custom_id="search")
            self.self_view = self_view

        @user_check
        async def callback(self, inter: disnake.MessageInteraction):
            await inter.response.send_modal(self.self_view.SearchModal())     

    class SearchModal(disnake.ui.Modal):
        def __init__(self):
            components = [
                disnake.ui.TextInput(
                    label="ID",
                    placeholder="Цифровой ID сообщения с идеей",
                    custom_id="idea_id",
                    style=disnake.TextInputStyle.short,
                    max_length=32
                ),
            ]
            super().__init__(title="Поиск идеи", custom_id="search", components=components)

        async def callback(self, inter: disnake.ModalInteraction):
            await inter.response.defer(ephemeral=True)
            try:
                idea_id = int(inter.text_values['idea_id'])
                view = IdeaView(idea_id, inter.author, inter.guild)
                await inter.message.edit(embed=view.embed, view=view)
                await inter.delete_original_response()
            except:
                return await inter.edit_original_response("Идея с таким айди не найдена.")

    class IdeasDropdown(disnake.ui.StringSelect):
        def __init__(self, self_view, options):
            super().__init__(
                custom_id="select_idea",
                placeholder="Выбери идею для просмотра.",
                options=options,
            )
            self.self_view = self_view 

        @user_check
        async def callback(self, inter: disnake.MessageInteraction):
            await inter.response.defer()
            idea_id = inter.values[0]
            view = IdeaView(idea_id=idea_id, user=inter.author, guild=inter.guild)
            await inter.message.edit(embed=view.embed, view=view)

    class SortDropdown(disnake.ui.StringSelect):
        def __init__(self, self_view):
            self.self_view = self_view
            sort_by = self_view.sort_by

            options = [
                SelectOption(label="Сортировать по лайкам", value="likes", description="Сортировка идей по количеству лайков", emoji="👍", default=True if sort_by == "likes" else False),
                SelectOption(label="Сортировать по дизлайкам", value="dislikes", description="Сортировка идей по количеству дизлайков", emoji="👎", default=True if sort_by == "dislikes" else False),
                SelectOption(label="Сортировать по названию", value="name", description="Сортировка идей по алфавиту", emoji="🔤", default=True if sort_by == "name" else False),
                SelectOption(label="Сортировать по ID", value="id", description="Сортировка идей по ID", emoji="🆔", default=True if sort_by == "id" else False),
            ]

            super().__init__(
                custom_id="select_sort",
                placeholder="Изменить сортировку.",
                options=options
            )

        @user_check
        async def callback(self, inter: disnake.MessageInteraction):
            await inter.response.defer()

            sort = inter.values[0]

            self.self_view.sort_by = sort
            self.self_view.update_page()

            await inter.message.edit(embed=self.self_view.embed, view=self.self_view)


class IdeaView(disnake.ui.View):
    def __init__(self, idea_id, user, guild):
        super().__init__(timeout=None)
        self.idea_id = idea_id
        self.user = user
        self.guild = guild
        self.add_item(self.AcceptButton(self))
        self.add_item(self.DeclineButton(self))
        self.add_item(self.DeleteButton(self))
        self.add_item(self.BackButton(self))
        if user:
          self.embed()

    def embed(self):
        idea = get_idea(self.idea_id)
        name, description, likes, dislikes, answer, idea_id, authorid = idea
        try:
            author = self.guild.get_member(authorid)
            author = author.name
        except:
            author = "—"

        self.embed = methods.embed(
            "Просмотр идеи",f"""
            ・**Название:** {name} 
            ・**Описание:** {description}
            ・**Лайки:** {likes} 👍
            ・**Дизлайки:** {dislikes} 👎
            ・**Автор:** {author}
            ・**Ответ:** {answer or "—"}
            ・*ID: {idea_id}*"""
        )

    class AcceptButton(disnake.ui.Button):
        def __init__(self, self_view):
            super().__init__(label="Принять", custom_id="accept", style=disnake.ButtonStyle.green, emoji="✅")
            self.self_view = self_view

        @user_check
        async def callback(self, inter: disnake.MessageInteraction):
            await inter.response.send_modal(self.self_view.AnswerModal(self_view=self.self_view, raw_answer="Принято", message=inter.message))

    class DeclineButton(disnake.ui.Button):
        def __init__(self, self_view):
            super().__init__(label="Отклонить", custom_id="decline", style=disnake.ButtonStyle.green, emoji="❎")
            self.self_view = self_view

        @user_check
        async def callback(self, inter: disnake.MessageInteraction):
            await inter.response.send_modal(self.self_view.AnswerModal(self_view=self.self_view, raw_answer="Отклонено", message=inter.message))

    class DeleteButton(disnake.ui.Button):
        def __init__(self, self_view):
            super().__init__(label="Удалить", custom_id="delete", style=disnake.ButtonStyle.red, emoji="🗑")
            self.self_view = self_view

        @user_check
        async def callback(self, inter: disnake.MessageInteraction):
            await inter.response.defer()
            with sqlite3.connect("ideas.db") as db:
                cursor = db.cursor()
                cursor.execute("DELETE FROM ideas WHERE id = ?", (self.self_view.idea_id,))
                db.commit()

            channel = inter.guild.get_channel(IDEA_CHANNEL_ID)
            try:
                message = await channel.fetch_message(self.self_view.idea_id)
                await message.delete()
            except:
                pass

            embed = methods.embed("Удаление идеи", "Ты успешно удалил идею!")
            await inter.message.edit(embed=embed, components=[self.self_view.BackButton(self.self_view)])

    class BackButton(disnake.ui.Button):
        def __init__(self, self_view):
            super().__init__(label="Назад", custom_id="back_to_select", style=disnake.ButtonStyle.gray)
            self.self_view = self_view

        @user_check
        async def callback(self, inter: disnake.MessageInteraction):
            await inter.response.defer()
            view = IdeasView(self.self_view.user)
            await inter.message.edit(embed=view.embed, view=view)

    class AnswerModal(disnake.ui.Modal):
        def __init__(self, self_view, raw_answer, message):
            self.message = message
            self.self_view = self_view
            self.raw_answer = raw_answer

            if self.raw_answer == "Принято":
                label = "Причина одобрения идеи"
                placeholder = "Введите причину одобрения."
            else:
                label = "Причина отклонения идеи"
                placeholder = "Введите причину отклонения."

            components = [
                disnake.ui.TextInput(
                    label=label,
                    placeholder=placeholder,
                    custom_id="reason",
                    style=disnake.TextInputStyle.short,
                    max_length=1024,
                ),
            ]
            super().__init__(title="Ответ на идею", custom_id="answer_idea", components=components)

        async def callback(self, inter: disnake.ModalInteraction):
            try: 
                await inter.response.defer(ephemeral=True)

                channel = inter.guild.get_channel(int(IDEA_CHANNEL_ID))
                message = await channel.fetch_message(self.self_view.idea_id)

                if self.raw_answer == "Отклонено":
                    answer = '❌ Отклонено'
                    color = disnake.Colour.from_rgb(252, 200, 200)
                elif self.raw_answer == 'Принято':
                    answer = '✅ Принято'
                    color = disnake.Colour.from_rgb(200, 252, 200)

                reason = inter.text_values['reason']

                embed = message.embeds[0]
                embed.remove_field(2)
                embed.add_field(name=answer, value=reason, inline=False)
                embed.color = color
                
                await message.edit(embed=embed, components=[])

                thread = message.thread
                if thread:
                    await thread.edit(locked=True)

                with sqlite3.connect("ideas.db") as db:
                    cursor = db.cursor()
                    cursor.execute("UPDATE ideas SET answer = ? WHERE id = ?", (self.raw_answer, self.self_view.idea_id))
                    db.commit()
                    try:
                        authorid = cursor.execute("SELECT author_id FROM ideas WHERE id = ?", (int(self.self_view.idea_id),)).fetchone()[0]
                        author = await inter.guild.fetch_member(authorid)
                        embed = methods.embed("Ты получил ответ на свою идею", f"**{answer}**\n{reason}\n{message.jump_url}")
                        await author.send(embed=embed)
                    except:
                        pass

                await inter.edit_original_response(f'Ты успешно ответил на идею {message.jump_url}')
                view = IdeasView(self.self_view.user)
                await self.message.edit(embed=view.embed, view=view)
            except:
                embed = methods.error("Неизвестная идея.")
                await self.message.edit(embed=embed, components=[disnake.ui.Button(label="Назад", custom_id="back_to_select", style=disnake.ButtonStyle.gray)])

class IdeasCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Показывает список идей без ответа.")
    @commands.default_member_permissions(manage_threads=True, manage_messages=True)
    async def ideas(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        view = IdeasView(inter.author)
        await inter.edit_original_response(embed=view.embed, view=view)

def setup(bot: commands.Bot):
    methods.startprint(__name__)
    bot.add_cog(IdeasCommand(bot))