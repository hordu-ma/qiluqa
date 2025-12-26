class DictUtil:

    @staticmethod
    def get_intention_with_bool(param: dict, key: str) -> bool:
        if not param:
            return False

        val = param.get(key) or ""
        if val in ('是', 'Y', 'y'):
            return True
        else:
            return False


if __name__ == "__main__":
    print(DictUtil.get_intention_with_bool(param={}, key="a"))
