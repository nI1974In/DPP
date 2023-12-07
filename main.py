import pandas as pd
from dataclasses import dataclass
import copy


@dataclass
class Recruit:
    id: int
    surname: str
    firstname: str
    patronymic: str
    category: str
    physical: int
    psychological: int
    priority: list[str]


@dataclass
class Military:
    branch: str
    recruits_amount: int
    min_category: str
    min_physical: int
    min_psychological: int


recruits, militaries = list(), dict()

conscript = pd.read_excel("res/conscript.xlsx")
for i in range(conscript.shape[0]):
    recruit = conscript.iloc[i, :]
    recruits.append(Recruit(id=recruit['ID'], surname=recruit['Фамилия'], firstname=recruit['Имя'],
                            patronymic=recruit['Отчество'], category=recruit['Категория годности'],
                            physical=recruit['Физическая оценка'], psychological=recruit['Психологическая оценка'],
                            priority=list(recruit[7:])))

army = pd.read_excel("res/military.xlsx")
for i in range(army.shape[0]):
    military = army.iloc[i, :]
    militaries[military['Род войск']] = Military(branch=military['Род войск'],
                                                 recruits_amount=military['Количество набираемых призывников'],
                                                 min_category=military['Минимальная категория годности'],
                                                 min_physical=military['Минимальный балл физподготовки'],
                                                 min_psychological=military['Минимальный балл психологического отбора'])


def MCSD(subjects: list[Recruit], objects: dict[str, Military]) -> list[tuple[int, str]]:
    subjects = copy.deepcopy(subjects)
    objects = copy.deepcopy(objects)

    res: list[tuple[int, str]] = list()

    for iteration in range(len(objects)):
        for i in range(len(subjects)-1, -1, -1):
            subject = subjects[i]
            object_element = objects[subject.priority[iteration]]
            if object_element.min_category == 'А' and subject.category == 'Б':
                continue
            if object_element.min_physical > subject.physical or object_element.min_psychological > subject.psychological:
                continue
            if object_element.recruits_amount > 0:
                res.append((subject.id, object_element.branch))
                object_element.recruits_amount -= 1
                del subjects[i]
    return res


def GS(subjects: list[Recruit], objects: dict[str, Military]) -> list[tuple[int, str]]:
    """
    Реализация алгоритма Гейла-Шепли
    Так как этот алгоритм используеет двустороннюю приоретизацию (т.е. и субъекты, и объекты имеют приоритеты), то
    необходимо назначить правило оценивания субъектов
    В контексте данной задачи будет использовано следующее правило:
    1) В любом случае признак призывника "Категория годности" важнее признака "Физическая оценка"
    2) В любом случае признак призывника "Физическая оценка" важнее признака "Психологическая оценка"
    3) Призывник с категорией А имеет более высокий приоритет, чем призывник с категорией Б
    4) В случае совпадения признаков "Категория годности", "Физическая оценка" и "Психологическая оценка", призывники
    имеют равный приоритет и распределяются в зависимости от решения алгоритма (в зависимости от места в списке)

    Чтобы не производить данную операцию сравнения большое количество раз, можно дать каждому субъекту оценку в
    зависимости от признаков с помощью следующего правила конвертации:
    0) У каждого призывника 0 очков
    1) "Психологическая оценка" прибавляется к количеству очков
    2) "Физическая оценка" умножается на 1000 и прибавляется к количеству очков
    3) Если "Категория годности" равна 'А', то к количеству очков прибавляется 1_000_000
    """
    subjects = [{'recruit': item, 'score': item.psychological + 1000 * item.physical + 1_000_000 if item.category == 'А' else 0} for item in copy.deepcopy(subjects)]
    objects = {item[0]: {'military': item[1], 'recruits': list()} for item in copy.deepcopy(objects).items()}

    res: list[tuple[int, str]] = list()

    # Первая итерация алгоритма, начальное заполнение
    for subject_index in range(len(subjects)-1, -1, -1):
        subject = subjects[subject_index]['recruit']
        while subject.priority.__len__() > 0:
            object_element = objects[subject.priority[0]]['military']
            if object_element.min_category == 'А' and subject.category == 'Б':
                del subject.priority[0]
                continue
            if object_element.min_physical > subject.physical or object_element.min_psychological > subject.psychological:
                del subject.priority[0]
                continue
            break
        else:
            continue
        objects[subject.priority[0]]['recruits'].append((subject, subjects[subject_index]['score']))
        del subject.priority[0]

    flag = True
    while flag:
        flag = False
        for object_index in objects:
            objects[object_index]['recruits'] = sorted(objects[object_index]['recruits'], key=lambda x: x[1], reverse=True)
            if objects[object_index]['recruits'].__len__() > objects[object_index]['military'].recruits_amount:
                flag = True
                for subject_index in range(objects[object_index]['recruits'].__len__() - 1, objects[object_index]['military'].recruits_amount - 1, -1):
                    # print(objects[object_index]['recruits'][subject_index])
                    subject = objects[object_index]['recruits'][subject_index][0]
                    while subject.priority.__len__() > 0:
                        object_element = objects[subject.priority[0]]['military']
                        if object_element.min_category == 'А' and subject.category == 'Б':
                            del subject.priority[0]
                            continue
                        if object_element.min_physical > subject.physical or object_element.min_psychological > subject.psychological:
                            del subject.priority[0]
                            continue
                        break
                    else:
                        del objects[object_index]['recruits'][subject_index]
                        continue
                    objects[subject.priority[0]]['recruits'].append(objects[object_index]['recruits'][subject_index])
                    del subject.priority[0]
                    del objects[object_index]['recruits'][subject_index]

    for object_index in objects:
        for subject in objects[object_index]['recruits']:
            res.append((subject[0].id, object_index))

    return res


def TTC(subjects: list[Recruit], objects: dict[str, Military]) -> list[tuple[int, str]]:
    subjects = copy.deepcopy(subjects)
    objects = copy.deepcopy(objects)

    res: list[tuple[int, str]] = list()

    for subject_index in range(len(subjects)-1, -1, -1):
        for priority_index in range(len(subjects[subject_index].priority)-1, -1, -1):
            subject = subjects[subject_index]
            object_element = objects[subject.priority[priority_index]]
            if object_element.min_category == 'А' and subject.category == 'Б':
                del subject.priority[priority_index]
                continue
            if object_element.min_physical > subject.physical or object_element.min_psychological > subject.psychological:
                del subject.priority[priority_index]
                continue
        if subjects[subject_index].priority.__len__() == 0:
            del subjects[subject_index]
        elif subjects[subject_index].priority.__len__() == 1 and objects[subjects[subject_index].priority[0]].recruits_amount > 0:
            res.append((subjects[subject_index].id, subjects[subject_index].priority[0]))
            del subjects[subject_index]
            objects[subjects[subject_index].priority[0]].recruits_amount -= 1
        elif subjects[subject_index].priority.__len__() == 1:
            del subjects[subject_index]

    for iteration in range(len(objects)):
        for i in range(len(subjects)-1, -1, -1):
            subject = subjects[i]
            if len(subject.priority) <= iteration:
                continue
            object_element = objects[subject.priority[iteration]]
            if object_element.recruits_amount > 0:
                res.append((subject.id, object_element.branch))
                object_element.recruits_amount -= 1
                del subjects[i]

    return res


if __name__ == '__main__':
    print(len(MCSD(recruits, militaries)))
    print(len(GS(recruits, militaries)))
    print(len(TTC(recruits, militaries)))
