import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvEntity } from '@vsolv/dev-kit/nest';
import { Column, CreateDateColumn, JoinColumn, ManyToOne, PrimaryColumn, UpdateDateColumn } from 'typeorm';
import { CoverageEntity } from '../../coverage';
import { ExclusionAggregate } from '../models';

@VsolvEntity({ prefix: 'exc', name: 'warranty_exclusion' }, 'tenant')
export class ExclusionEntity {
  @PrimaryColumn()
  id!: string;

  @Column({ nullable: true })
  referenceId!: string | null;

  @CreateDateColumn()
  created!: Date;

  @UpdateDateColumn()
  modified!: Date;

  @Column()
  title!: string;

  @Column()
  description!: string;

  @Column()
  coverageId!: string;

  @JoinColumn({ name: 'coverageId' })
  @ManyToOne(() => CoverageEntity)
  coverage?: CoverageEntity;

  toAggregate(publisher?: EventPublisher): ExclusionAggregate {
    return mergeObjectContext(
      new ExclusionAggregate({
        id: this.id,
        referenceId: this.referenceId,

        created: this.created,
        modified: this.modified,

        title: this.title,
        description: this.description,
      }),
      publisher
    );
  }
}
