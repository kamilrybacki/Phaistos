import pydantic


class Test(pydantic.BaseModel):
    a: int
    b: str
    c: float


def validate_model(self: Test):
    print(self.dict())
    return self


test = pydantic.create_model(
    'TestPlus',
    __base__=(Test,),
    __validators__={
        'model': pydantic.model_validator(mode='after')(validate_model)
    }
)
test(a=1, b='2', c=3.0)
