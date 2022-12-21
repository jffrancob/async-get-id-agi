class Slider():

    def digits(self, number):
        return [x for x in number]

    def id(self, id_number):
        if len(id_number) == 8:
            return [id_number[0:2], id_number[2], id_number[3:5], id_number[5], id_number[6:8]]
        elif len(id_number) == 7:
            return [id_number[0], id_number[1], id_number[2:4], id_number[4], id_number[5:7]]
        elif len(id_number) == 10:
            return [id_number[0], id_number[1], id_number[2:4],
                    id_number[4], id_number[5:7], id_number[7], id_number[8:10]]
        elif len(id_number) == 6:
            return [id_number[0], id_number[1:3], id_number[3], id_number[4:6]]
        else:
            return [x for x in id_number]

    def phone(self, phone):
        if len(phone) == 7:
            return [phone[0], phone[1:3], phone[3:5], phone[5:7]]
        elif len(phone) == 10 and phone.startswith("30"):
            return [phone[0:3], phone[3:4], phone[4:6], phone[6:8], phone[8:10]]
        elif len(phone):
            return [phone[0], phone[1:3], phone[3:4], phone[4:6], phone[6:8], phone[8:10]]
        else:
            return [phone]

    def code(self, code):
        if len(code) == 3:
            return [code[0], code[1:3]]
        else:
            return [code]
